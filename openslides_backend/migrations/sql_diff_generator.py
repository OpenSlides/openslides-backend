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
from meta.dev.src.generate_sql_schema import GenerateCodeBlocks, Helper
from meta.dev.src.helper_get_names import HelperGetNames
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
    GenerateCodeBlocks.generate_the_code()
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
        sql += GenerateCodeBlocks.table_sql.get(collection_name, "")
    for collection_name in add:
        found.add(collection_name)
        sql += GenerateCodeBlocks.alter_table_final_sql.get(collection_name, "")
    for collection_name in add:
        found.add(collection_name)
        sql += GenerateCodeBlocks.trigger_sql.get(collection_name, "")
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
        model_def_new = CURR_MODELS[collection_name_new]["fields"]
        trigger_names_new = get_trigger_names(collection_name_new, model_def_new)
        model_def_old = PREV_MODELS[collection_name_old]["fields"]
        trigger_names_old = get_trigger_names(collection_name_old, model_def_old)
        for field_name, field_old in trigger_names_old.items():
            if atf_old := field_old.get("alter_table_final"):
                atf_new = trigger_names_new[field_name]["alter_table_final"]
                constraint_name_new = atf_new[0]
                constraint_name_old = atf_old[0]
                idx_name_new = atf_new[1]
                idx_name_old = atf_old[1]
                result += f"ALTER INDEX {idx_name_old} RENAME TO {idx_name_new};\n"
                result += f"ALTER TABLE {table_name_new} RENAME CONSTRAINT {constraint_name_old} TO {constraint_name_new};\n"
            for trigger_key in TRIGGER_KEYS:
                if tk_old := field_old.get(trigger_key):
                    tk_new = trigger_names_new[field_name][trigger_key]
                    for trigger_name_new, trigger_name_old in zip(tk_new, tk_old):
                        result += f"ALTER TRIGGER {trigger_name_old} ON {table_name_new} RENAME TO {trigger_name_new};\n"
        del dc_rename_dict[0][collection_name_old]

    for collection_name, collection_diff in field_renames.items():
        dc_collection = cast(dict, dc_rename_dict[1][collection_name])
        for field_name_old, field_name_new in collection_diff.items():
            assert isinstance(field_name_new, str)
            field_def = CURR_MODELS[collection_name]["fields"][field_name_new]
            is_view_field = False
            if field_def.get("to"):
                # This also includes all sql fields
                is_view_field, *_ = get_view_field_state_write_fields(
                    collection_name, field_name_new, field_def
                )
            result += AlterSchemaHelper.get_rename_view_column(
                collection_name, field_name_old, field_name_new
            )
            if not is_view_field:
                result += AlterSchemaHelper.get_rename_table_column(
                    HelperGetNames.get_table_name(collection_name),
                    field_name_old,
                    field_name_new,
                )

            # TODO recreate dependend triggers and intermediate tables
            del dc_collection[field_name_old]
        # TODO Renaming and redefining constraints
        remove_empty(dc_rename_dict[1], collection_name)
    return result


def get_trigger_names(
    collection_name: str, fields: dict[str, Any]
) -> dict[str, dict[str, list[str]]]:
    schema_zone_texts_per_field: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    errors: list[str] = []

    for fname, fdata in fields.items():
        method_or_str, type_ = GenerateCodeBlocks.get_method(fname, fdata)
        if isinstance(method_or_str, str):
            error = Helper.prefix_error(method_or_str, collection_name, fname)
            schema_zone_texts_per_field[fname]["undecided"].append(error)
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
                    schema_zone_texts_per_field[fname][k].append(matched.group(1))
                    schema_zone_texts_per_field[fname][k].append(matched.group(2))
                elif k in TRIGGER_KEYS and (
                    matched := re.search(r"TRIGGER\s+(\w+)\s+AFTER", v, re.DOTALL)
                ):
                    schema_zone_texts_per_field[fname][k].append(matched.group(1))
                else:
                    errors.append(
                        Helper.prefix_error(
                            "Could not extract " + k, collection_name, fname
                        )
                    )
            if error:
                errors.append(Helper.prefix_error(error, collection_name, fname))
    return schema_zone_texts_per_field


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
