import os
import re
import sys
from argparse import ArgumentParser
from collections import defaultdict
from copy import deepcopy
from typing import Any, cast

import simplejson as json

from cli.util.util import get_view_field_state_write_fields
from meta.dev.src.alter_schema_helper import AlterSchemaHelper
from meta.dev.src.generate_sql_schema import (
    FieldSqlErrorType,
    GenerateCodeBlocks,
    Helper,
    TableFieldType,
)
from meta.dev.src.helper_get_names import HelperGetNames, InternalHelper
from meta.dev.src.typing import SchemaZoneKey
from openslides_backend.migrations.migration_helper import (
    MIGRATIONS_PATH,
    MigrationHelper,
)
from openslides_backend.migrations.yaml_diff_generator import (
    CURR_MODELS,
    PREV_MODELS,
    RENAMES,
    Renames,
    dumpjson,
    generate_diff,
)
from openslides_backend.shared.exceptions import BadCodingException

TRIGGER_KEYS: list[SchemaZoneKey] = [
    "create_trigger_partitioned_sequences",
    "create_trigger_1_1_relation_not_null",
    "create_trigger_1_n_relation_not_null",
    "create_trigger_n_m_relation_not_null",
    "create_trigger_prevent_updates_code",
    "create_trigger_unique_ids_pair_code",
    "create_trigger_equal_fields_code",
    "create_trigger_notify",
]


def get_schema_sql_dict() -> dict[str, dict[str, str]]:
    return {
        "table_sql": deepcopy(GenerateCodeBlocks.table_sql),
        "alter_table_final_sql": deepcopy(GenerateCodeBlocks.alter_table_final_sql),
        "view_sql": deepcopy(GenerateCodeBlocks.view_sql),
        "trigger_sql": deepcopy(GenerateCodeBlocks.trigger_sql),
        "intermediate_sql": deepcopy(GenerateCodeBlocks.intermediate_sql),
    }


# TODO use context
InternalHelper.MODELS = PREV_MODELS
GenerateCodeBlocks.generate_the_code()
PREV_CODE_BLOCKS = get_schema_sql_dict()
InternalHelper.MODELS = CURR_MODELS
GenerateCodeBlocks.generate_the_code()
CURR_CODE_BLOCKS = get_schema_sql_dict()

"""
This script works in conjunction with the yaml_diff_generator.py.
To use this script create a folder 'previous_models' next to it and copy the unchanged model diffinitions from the meta into it.
It will generate the sql diff comparing it to the changes made to the model definitions present in the meta.
The sql diff will be written to 'migrations/mig_[last migration number].*/schema_diff.sql'.
"""

alter_views: set[str] = set()


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--dumpjson", action="store_true")
    args = parser.parse_args()

    diff = generate_diff()
    diff_control: dict[str, Any] = deepcopy(diff)
    if args.dumpjson:
        dumpjson(diff)

    sql = "-- REMOVE SECTION --\n"
    # TODO create generate diff content functions in schema generator.
    # Using a lot of isinstance calls here for pleasing mypy
    remove = diff["remove"]
    if isinstance(remove, list) and isinstance(remove[0], list):
        for collection_name in remove[0]:
            sql += f"DROP TABLE {HelperGetNames.get_table_name(collection_name)} CASCADE;\n"
            diff_control["remove"][0].remove(collection_name)
    if isinstance(remove, list) and isinstance(remove_tree_dict := remove[1], dict):
        sql += handle_remove_tree(remove_tree_dict, diff_control["remove"][1])

    sql += "\n-- RENAME SECTION --\n"
    sql += handle_rename(diff["rename"], diff_control["rename"])

    sql += "\n-- ADD SECTION --\n"
    add = diff["add"]
    if isinstance(add, tuple) and isinstance(add[0], dict):
        sql += generate_new_collection_sql(add[0], diff_control["add"][0]).lstrip("\n")
    if isinstance(add, tuple) and isinstance(add_tree_dict := add[1], dict):
        sql += handle_add_tree(add_tree_dict, diff_control["add"][1])

    sql += "\n-- EDIT SECTION --\n"
    edit = diff["edit"]
    if isinstance(edit, tuple) and isinstance(edit_dict := edit[1], dict):
        sql += handle_edit_tree(edit_dict, diff_control["edit"][1])

    sql += "\n-- VIEWS UPDATE SECTION --\n"
    view_sql = "".join(
        GenerateCodeBlocks.view_sql[collection_name]
        for collection_name in sorted(alter_views)
    )
    sql += view_sql.replace("CREATE", "CREATE OR REPLACE").lstrip("\n")
    with open(
        os.path.join(
            MIGRATIONS_PATH,
            MigrationHelper.get_last_migration_directory(),
            "schema_diff.sql",
        ),
        "w",
    ) as f:
        f.write(sql)

    for dict_name in diff:
        remove_empty(diff_control, dict_name)
    # assert not diff, f"Diff control still contains:\n{diff}"
    if diff_control:
        print("Diff control still contains:\n" + json.dumps(diff_control, indent=2))
        return 1
    return 0


def remove_empty(dictionary: dict[str, Any], key: str) -> None:
    if not any(dictionary[key]):
        del dictionary[key]


def generate_new_collection_sql(add: dict[str, Any], dc_add: dict[str, Any]) -> str:
    sql = ""
    found = set()
    for collection_name in add:
        found.add(collection_name)
        sql += GenerateCodeBlocks.table_sql[collection_name]
    for collection_name in add:
        found.add(collection_name)
        sql += GenerateCodeBlocks.alter_table_final_sql.get(collection_name, "")
    for collection_name in add:
        found.add(collection_name)
        sql += GenerateCodeBlocks.trigger_sql[collection_name]
    for collection_name in add:
        found.add(collection_name)
        sql += GenerateCodeBlocks.intermediate_sql.get(collection_name, "")
    for collection_name in found:
        del dc_add[collection_name]
        alter_views.add(collection_name)
    return sql


def handle_add_field_attributes(
    table_name: str,
    field_name: str,
    field_def_diff: dict[str, Any],
    dc_field_def: dict[str, Any],
) -> str:
    constraints_sql = ""
    collection_name = table_name[:-2]
    for constraint, value in field_def_diff.items():
        """
        TODO other constraints type etc
        This is a full list of leaf types we have. (Including _meta.)
        Some of which aren't constraints but need to be implemented/considered elsewhere.

        languages
        ballot_paper_selection
        poll_backends
        onehundred_percent_bases
        type
        restriction_mode
        constant
        required
        enum
        description
        default
        minimum
        read_only
        reference
        collections
        field
        equal_fields
        to
        on_delete
        sequence_scope
        unique_together
        constant_legacy
        unique
        sql
        log_triggers
        unique_together_strict
        maxLength
        maximum
        calculated
        minLength
        """
        match constraint:
            case "type":
                match value:
                    case "color":
                        constraints_sql += Helper.get_inline_color_constraint(
                            table_name, field_name
                        )
                    case "timezone":
                        constraints_sql += Helper.get_inline_timezone_constraint(
                            table_name, field_name
                        )
                    case (
                        "string"
                        | "number"
                        | "boolean"
                        | "JSON"
                        | "HTMLStrict"
                        | "HTMLPermissive"
                        | "float"
                        | "decimal(6)"
                        | "timestamp"
                        | "string[]"
                        | "number[]"
                        | "text"
                        | "text[]"
                    ):
                        pass
                    case (
                        "relation"
                        | "relation-list"
                        | "generic-relation"
                        | "generic-relation-list"
                    ):
                        # TODO
                        pass
                    case _:
                        raise NotImplementedError(
                            f"{table_name}/{field_name}: {constraint}, {value}"
                        )
            case "constant":
                # TODO
                pass
            case "required":
                constraints_sql += Helper.get_inline_required_constraint(
                    table_name, field_name
                )
            case "enum":
                # TODO
                pass
            case "equal_fields":
                # TODO
                pass
            case "sequence_scope":
                # TODO
                pass
            case "unique":
                constraints_sql += Helper.get_inline_unique_constraint(
                    table_name, field_name
                )
            case "unique_together_strict":
                # TODO
                pass
            case "maximum":
                constraints_sql += Helper.get_inline_maximum_constraint(
                    table_name, field_name, value
                )
            case "minimum":
                constraints_sql += Helper.get_inline_minimum_constraint(
                    table_name, field_name, value
                )
            case "maxLength":
                # TODO
                pass
            case "minLength":
                constraints_sql += Helper.get_inline_minlength_constraint(
                    table_name, field_name, value
                )
            case "default":
                constraints_sql += Helper.get_inline_default_constraint(
                    table_name, field_name, value
                )
            case "sql":
                alter_views.add(collection_name)
            case "to":
                # This essentially would be an integer field being turned into a real relation
                # Should probably be handled together with reference and type
                # TODO
                is_view_field, _, write_fields = get_view_field_state_write_fields(
                    collection_name,
                    field_name,
                    CURR_MODELS[collection_name]["fields"][field_name],
                )
                alter_views_conditionally(
                    collection_name, bool(write_fields), is_view_field
                )
            case "reference":
                # TODO
                pass
            case "restriction_mode" | "description" | "on_delete" | "constant_legacy":
                # this is irrelevant, thus omitted
                pass
            case _:
                raise NotImplementedError(
                    f"{table_name}/{field_name}: {constraint}, {value}"
                )
        del dc_field_def[constraint]
    return constraints_sql


def handle_edit_field_attributes(
    table_name: str,
    field_name: str,
    field_def_diff: dict[str, Any],
    dc_field_def: tuple[dict[str, Any], dict[str, Any]],
) -> str:
    constraints_sql = ""
    collection_name = table_name[:-2]
    for constraint, value in field_def_diff.items():
        field_def = CURR_MODELS[collection_name]["fields"][field_name]
        match constraint:
            case "default":
                default = Helper.get_formatted_default_value(
                    table_name, field_name, field_def_diff["default"], field_def["type"]
                )
                constraints_sql += f"ALTER TABLE {table_name} ALTER COLUMN {field_name} SET DEFAULT {default};\n"
            case "description":
                pass
            case "sql":
                alter_views.add(collection_name)
            case "reference" | "to":
                if table_name in RENAMES[0] or field_name in RENAMES[1].get(
                    table_name, {}
                ):
                    # Shouldn't be a case since this is already skipped in yaml diff generator.
                    # TODO decide whether to fail or delete this check
                    print(
                        f"Skipping {table_name}/{field_name} 'to' attribute since it is renamed."
                    )
                    continue
                else:
                    NotImplementedError(
                        f"{constraint}: {value} is probably a view field or unmentioned in renames."
                    )

                is_view_field, _, write_fields = get_view_field_state_write_fields(
                    collection_name,
                    field_name,
                    CURR_MODELS[collection_name]["fields"][field_name],
                )
                alter_views_conditionally(
                    collection_name, bool(write_fields), is_view_field
                )
                # TODO recreate affected triggers
            case _:
                raise NotImplementedError(f"{constraint}: {value}")
        del dc_field_def[0][constraint]
    return constraints_sql


def handle_rename(renames: Renames, dc_rename_dict: Renames) -> str:
    result = ""
    collection_renames = renames[0]
    field_renames = renames[1]

    for collection_name_old, collection_name_new in collection_renames.items():
        table_name_new = HelperGetNames.get_table_name(collection_name_new)
        result += AlterSchemaHelper.get_rename_table(
            HelperGetNames.get_table_name(collection_name_old), table_name_new
        )
        result += AlterSchemaHelper.get_rename_view(
            collection_name_old, collection_name_new
        )
        collection_def_new = CURR_MODELS[collection_name_new]["fields"]
        dependent_renames_new = get_dependent_renames(
            collection_name_new, collection_def_new
        )
        collection_def_old = PREV_MODELS[collection_name_old]["fields"]
        dependent_renames_old = get_dependent_renames(
            collection_name_old, collection_def_old
        )
        for field_name in collection_def_old:
            result += rename_inline_constraint_sql(
                collection_name_old, collection_name_new, field_name, field_name
            )
        for field_name, field_old in dependent_renames_old.items():
            result += generate_dependent_field_sql(
                table_name_new, field_old, dependent_renames_new[field_name]
            )
        del dc_rename_dict[0][collection_name_old]

    for collection_name, collection_diff in field_renames.items():
        dc_collection = cast(dict, dc_rename_dict[1][collection_name])
        collection_def_new = CURR_MODELS[collection_name]["fields"]
        dependent_renames_new = get_dependent_renames(
            collection_name, collection_def_new
        )
        collection_def_old = PREV_MODELS[collection_name]["fields"]
        # TODO use context
        GenerateCodeBlocks.intermediate_tables = dict()
        InternalHelper.MODELS = PREV_MODELS
        dependent_renames_old = get_dependent_renames(
            collection_name, collection_def_old
        )
        InternalHelper.MODELS = CURR_MODELS
        for field_name_old, field_name_new in collection_diff.items():
            assert isinstance(field_name_new, str)
            result += rename_inline_constraint_sql(
                collection_name, collection_name, field_name_old, field_name_new
            )
            field_def = collection_def_new[field_name_new]
            is_view_field = False
            if field_def.get("to"):
                # This also includes all sql fields
                is_view_field, *_ = get_view_field_state_write_fields(
                    collection_name, field_name_new, field_def
                )
            result += AlterSchemaHelper.get_rename_view_column(
                collection_name, field_name_old, field_name_new
            )
            # TODO rename intermediate table column
            if not is_view_field:
                result += AlterSchemaHelper.get_rename_table_column(
                    HelperGetNames.get_table_name(collection_name),
                    field_name_old,
                    field_name_new,
                )
            result += generate_dependent_field_sql(
                HelperGetNames.get_table_name(collection_name),
                dependent_renames_old[field_name_old],
                dependent_renames_new[field_name_new],
            )
            del dc_collection[field_name_old]
        # TODO Renaming and redefining constraints
        # TODO unique together constraints
        remove_empty(dc_rename_dict[1], collection_name)
    return result


def get_dependent_field_constraints(
    collection_name: str, code_blocks: dict[str, dict[str, str]]
) -> dict[str, list[str]]:
    result = defaultdict(list)
    table_def_parts = code_blocks.get("table_sql", {})[collection_name].split(",")
    # Delete table header and id.
    del table_def_parts[0]
    for table_def_part in table_def_parts:
        table_def_part = table_def_part.strip()
        field_name, table_def_part = table_def_part.split(" ", maxsplit=1)
        field_name = field_name.strip()
        for matched in re.finditer(
            r"CONSTRAINT\s+(\w+)\s+(\w+)", table_def_part, re.DOTALL
        ):
            if matched[2] not in ("DEFAULT", "NOT"):
                # Required constraints with NOT NULL and DEFAULT constraints don't have a name.
                result[field_name].append(matched[1])
    return result


def rename_inline_constraint_sql(
    collection_name_old: str,
    collection_name_new: str,
    field_name_old: str,
    field_name_new: str,
) -> str:
    result = ""

    # TODO delete once FieldAttributes exists
    class FieldAttributes:
        skipped_in_schema = [
            "calculated",
            "constant_legacy",
            "deferred",
            "description",
            "on_delete",
            "read_only",
            "restriction_mode",
        ]

    diff_control = list(CURR_MODELS[collection_name_new]["fields"][field_name_new])
    enum_names_new: list[str] = []
    enum_names_old: list[str] = []
    constraint_names_new: list[str] = []
    constraint_names_old: list[str] = []
    for models_lookup, collection_name, field_name, names_list, enum_names in (
        (
            PREV_MODELS,
            collection_name_old,
            field_name_old,
            constraint_names_old,
            enum_names_old,
        ),
        (
            CURR_MODELS,
            collection_name_new,
            field_name_new,
            constraint_names_new,
            enum_names_new,
        ),
    ):
        field_def = models_lookup[collection_name]["fields"][field_name]
        for attr in sorted(field_def):
            name = None
            match attr:
                # TODO handle log_triggers field attribute
                case "default" | "required":
                    # Don't have names.
                    pass
                case "sql" | "equal_fields" | "constant" | "reference":
                    # Skipped out of separate reasons.
                    # "sql" View columns will always already be renamed.
                    # "equal_fields" | "constant" Generate triggers which are treated elsewhere.
                    # "reference" Covered by 'to'.
                    pass
                case "to":
                    # TODO intermediate table names and constraints
                    type_ = field_def["type"]
                    if type_ == "generic-relation-list":
                        foreign_table_fields: list[TableFieldType] = (
                            InternalHelper.get_definitions_from_foreign_list(
                                field_def.get("to"), field_def.get("reference")
                            )
                        )
                        for foreign_field in foreign_table_fields:
                            # TODO for 1g:1 and gm (unique, valid, fk, idx yes; generated always no) and more
                            pass
                    elif type_ == "relation":
                        foreign_table_field: TableFieldType = (
                            TableFieldType.get_definitions_from_foreign(
                                field_def.get("to"), field_def.get("reference")
                            )
                        )
                        state, *_ = InternalHelper.check_relation_definitions(
                            TableFieldType(collection_name, field_name_new, field_def),
                            [foreign_table_field],
                        )
                        # if is actual field
                        if state == FieldSqlErrorType.FIELD:
                            foreign_card, error = InternalHelper.get_cardinality(
                                foreign_table_field
                            )
                            if foreign_card.startswith("1"):
                                name = HelperGetNames.get_unique_constraint_name(
                                    collection_name, [field_name]
                                )
                case "minimum" | "maximum" | "minLength" | "unique":
                    constraint_name_func = getattr(
                        HelperGetNames,
                        f"get_{attr.lower()}_constraint_name",
                    )
                    name = constraint_name_func(
                        collection_name,
                        ([field_name] if attr == "unique" else field_name),
                    )
                    # result += AlterSchemaHelper.get_drop_table_constraint_statement(
                    #     collection_name, constraint_name
                    # )
                # case "sql":
                #     alter_views.add(collection_name)
                # case "constant":
                #     result += AlterSchemaHelper.get_drop_trigger_statement(
                #         collection_name,
                #         HelperGetNames.get_constant_field_trigger_name(
                #             collection_name, field_name
                #         ),
                #     )
                # case "equal_fields":
                #     with prev_models_context():
                #         EqualFieldsHelper.update_equal_fields_diff(
                #             collection_name, field_name
                #         )
                case "type":
                    match field_def["type"]:
                        case "timezone":
                            name = HelperGetNames.get_timezone_constraint_name(
                                collection_name, field_name
                            )
                        case "color":
                            name = HelperGetNames.get_color_constraint_name(
                                collection_name, field_name
                            )
                case "enum":
                    enum_names.append(
                        HelperGetNames.get_enum_name_for_column(
                            collection_name, field_name
                        )
                    )
                case value if value in FieldAttributes.skipped_in_schema:
                    pass
                case _:
                    # Skipped as not likely to be renamed in the foreseeable future:
                    # "sequence_scope": would require some dynamic name parsing
                    raise NotImplementedError(f"{collection_name}/{field_name}: {attr}")
            if name:
                names_list.append(name)
            if attr in diff_control:
                diff_control.remove(attr)
    assert not diff_control, f"{diff_control} left after attribute check of rename."
    for name_old, name_new in zip(enum_names_new, enum_names_old):
        result += AlterSchemaHelper.get_rename_enum(name_old, name_new)
    for name_old, name_new in zip(constraint_names_old, constraint_names_new):
        if name_old != name_new:
            # Using collection_name_new since tables will be renamed before.
            result += AlterSchemaHelper.get_rename_constraint(
                HelperGetNames.get_table_name(collection_name_new), name_old, name_new
            )
        else:
            BadCodingException(
                f"{collection_name_old}/{field_name_old}: Only fields or collections with changed names should be handled for inline constraint renames."
            )
    return result


def generate_dependent_field_sql(
    table_name_new: str,
    field_old: dict[str, Any],
    field_new: dict[str, Any],
) -> str:
    result = ""
    if atf_old := field_old.get("alter_table_final"):
        atf_new = field_new["alter_table_final"]
        constraint_name_new = atf_new[0]
        constraint_name_old = atf_old[0]
        idx_name_new = atf_new[1]
        idx_name_old = atf_old[1]
        result += AlterSchemaHelper.get_rename_index(idx_name_old, idx_name_new)
        result += AlterSchemaHelper.get_rename_constraint(
            table_name_new, constraint_name_old, constraint_name_new
        )
    for trigger_key in TRIGGER_KEYS:
        if tk_old := field_old.get(trigger_key):
            tk_new = field_new[trigger_key]
            for trigger_name_new, trigger_name_old in zip(tk_new, tk_old):
                result += AlterSchemaHelper.get_rename_trigger(
                    table_name_new, trigger_name_old, trigger_name_new
                )
    return result


def get_dependent_renames(
    collection_name: str, fields: dict[str, Any]
) -> dict[str, dict[str, list[str]]]:
    """Returns the triggers and fkey constraints of the 'alter table final' block for all given fields."""
    name_per_field_and_schemazonekey: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    errors: list[str] = []

    for fname, fdata in fields.items():
        method_or_str, type_ = GenerateCodeBlocks.get_method(fname, fdata)
        if isinstance(method_or_str, str):
            error = Helper.prefix_error(method_or_str, collection_name, fname)
            name_per_field_and_schemazonekey[fname]["undecided"].append(error)
            errors.append(error)
        else:
            result, error = method_or_str(collection_name, fname, fdata, type_)
            for k, v in result.items():
                assert isinstance(v, str)
                if k == "alter_table_final" and (
                    matched := re.search(
                        r"CONSTRAINT\s+(\w+)\s+FOREIGN.*?INDEX\s+(\w+)", v, re.DOTALL
                    )
                ):
                    name_per_field_and_schemazonekey[fname][k].append(matched.group(1))
                    name_per_field_and_schemazonekey[fname][k].append(matched.group(2))
                elif k in TRIGGER_KEYS and (
                    matched := re.search(r"TRIGGER\s+(\w+)\s+AFTER", v, re.DOTALL)
                ):
                    name_per_field_and_schemazonekey[fname][k].append(matched.group(1))
                else:
                    errors.append(
                        Helper.prefix_error(
                            "Could not extract " + k, collection_name, fname
                        )
                    )
            if error:
                errors.append(Helper.prefix_error(error, collection_name, fname))
    return name_per_field_and_schemazonekey


def alter_views_conditionally(
    collection_name: str, has_write_fields: bool, is_view_field: bool
) -> None:
    if has_write_fields or is_view_field:
        alter_views.add(collection_name)


def handle_remove_tree(
    remove_tree_dict: dict[str, tuple[dict[str, Any], dict[str, Any]]],
    dc_remove_tree_dict: dict[str, tuple[dict[str, Any], dict[str, Any]]],
) -> str:
    result = ""
    for collection_name, field_lists in remove_tree_dict.items():
        fields = field_lists[1]["fields"]
        for field_name in fields[0]:
            result += f"ALTER TABLE {collection_name}_t DROP COLUMN {field_name};\n"

            dc_remove_tree_dict[collection_name][1]["fields"][0].remove(field_name)
            # TODO fields[1]
            # constraints_sql += f"ALTER TABLE {table_name} ALTER COLUMN {field_name} DROP DEFAULT ;\n"
            remove_empty(dc_remove_tree_dict[collection_name][1], "fields")
        remove_empty(dc_remove_tree_dict, collection_name)
    return result


def handle_add_tree(
    add_tree_dict: dict[str, tuple[dict[str, Any], dict[str, Any]]],
    dc_add_tree_dict: dict[str, tuple[dict[str, Any], dict[str, Any]]],
) -> str:
    sql = ""
    for collection_name, collection_def in add_tree_dict.items():
        # TODO _meta
        table_name = HelperGetNames.get_table_name(collection_name)
        # TODO unique_together, unique_together_strict
        for fields_idx in [0, 1]:
            # fields always exists
            fields = collection_def[1]["fields"][fields_idx]
            dc_fields = dc_add_tree_dict[collection_name][1]["fields"][fields_idx]
            for field_name, field_def in fields.items():
                if fields_idx == 0:
                    # field added
                    constraints_sql = handle_add_field_attributes(
                        table_name, field_name, field_def, dc_fields[field_name]
                    )
                    sql += f"ALTER TABLE {table_name} ADD COLUMN {field_name}{constraints_sql};\n"
                else:
                    # field altered
                    sql += handle_edit_field_attributes(
                        table_name, field_name, field_def[0], dc_fields[field_name]
                    )
                remove_empty(
                    dc_add_tree_dict[collection_name][1]["fields"][fields_idx],
                    field_name,
                )
        remove_empty(dc_add_tree_dict[collection_name][1], "fields")
        remove_empty(dc_add_tree_dict, collection_name)
    return sql


def handle_edit_tree(
    edit_tree_dict: dict[str, tuple[dict[str, Any], dict[str, Any]]],
    dc_edit_tree_dict: dict[str, tuple[dict[str, Any], dict[str, Any]]],
) -> str:
    sql = ""
    for collection_name, collection_def in edit_tree_dict.items():
        table_name = HelperGetNames.get_table_name(collection_name)
        dc_fields = dc_edit_tree_dict[collection_name][1]["fields"][1]
        for field_name, field_def in collection_def[1]["fields"][1].items():
            sql += handle_edit_field_attributes(
                table_name, field_name, field_def[0], dc_fields[field_name]
            )
            remove_empty(dc_edit_tree_dict[collection_name][1]["fields"][1], field_name)
        remove_empty(dc_edit_tree_dict[collection_name][1], "fields")
        remove_empty(dc_edit_tree_dict, collection_name)
    return sql


if __name__ == "__main__":
    sys.exit(main())
