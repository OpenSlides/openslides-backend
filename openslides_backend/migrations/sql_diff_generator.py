import os
import sys
from argparse import ArgumentParser
from copy import deepcopy
from typing import Any, cast

import simplejson as json

from cli.util.util import get_view_field_state_write_fields
from meta.dev.src.alter_schema_helper import AlterSchemaHelper
from meta.dev.src.generate_sql_schema import GenerateCodeBlocks, Helper
from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.yaml_diff_generator import (
    CURR_MODELS,
    RENAMES,
    CollectionsRemoveList,
    EnumTypesRemoveDict,
    FieldAttributes,
    MetaAttributesRemoveList,
    RemoveDiffDict,
    Renames,
    dumpjson,
    generate_diff,
)
from openslides_backend.shared.exceptions import BadCodingException

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

    # Has to happen before remove: field types have to change before dropping the enum
    sql = "-- EDIT SECTION --\n"
    edit = diff["edit"]
    if isinstance(edit, tuple) and isinstance(edit_dict := edit[1], dict):
        sql += handle_edit_tree(edit_dict, diff_control["edit"][1])

    sql += "\n-- REMOVE SECTION --\n"
    # TODO create generate diff content functions in schema generator.
    # Using a lot of isinstance calls here for pleasing mypy
    remove: RemoveDiffDict | None = diff["remove"]
    if remove:
        sql += handle_remove(remove, diff_control["remove"])

    sql += "\n-- RENAME SECTION --\n"
    sql += handle_rename(diff["rename"], diff_control["rename"])

    sql += "\n-- ADD SECTION --\n"
    add = diff["add"]
    GenerateCodeBlocks.generate_the_code()
    if isinstance(add, tuple) and isinstance(add[0], dict):
        sql += generate_new_collection_sql(add[0], diff_control["add"][0]).lstrip("\n")
    if isinstance(add, tuple) and isinstance(add_tree_dict := add[1], dict):
        sql += handle_add_tree(add_tree_dict, diff_control["add"][1])

    sql += "\n-- VIEWS UPDATE SECTION --\n"
    view_sql = "".join(
        GenerateCodeBlocks.view_sql[collection_name]
        for collection_name in sorted(alter_views)
    )
    sql += view_sql.replace("CREATE", "CREATE OR REPLACE").lstrip("\n")
    # TODO Do this in a sub folder migrations?
    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
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
    if dictionary[key] is None or not any(dictionary[key]):
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
        result += AlterSchemaHelper.get_rename_table(
            HelperGetNames.get_table_name(collection_name_old),
            HelperGetNames.get_table_name(collection_name_new),
        )
        result += AlterSchemaHelper.get_rename_view(
            collection_name_old, collection_name_new
        )
        # TODO recreate dependend triggers
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


def alter_views_conditionally(
    collection_name: str, has_write_fields: bool, is_view_field: bool
) -> None:
    if has_write_fields or is_view_field:
        alter_views.add(collection_name)


def handle_remove(remove: RemoveDiffDict, dc_remove_dict: dict[str, Any]) -> str:
    result = ""
    if "collections" in remove:
        collections_remove_list: CollectionsRemoveList = remove["collections"]
        if isinstance(
            collection_names := collections_remove_list[0], list
        ) and isinstance(dc_collection_names := dc_remove_dict["collections"][0], list):
            for collection_name in collection_names:
                result += AlterSchemaHelper.get_drop_table_statement(collection_name)
                dc_collection_names.remove(collection_name)
        if isinstance(
            remove_tree_dict := collections_remove_list[1], dict
        ) and isinstance(dc_remove_tree_dict := dc_remove_dict["collections"][1], dict):
            result += handle_remove_tree(remove_tree_dict, dc_remove_tree_dict)
        remove_empty(dc_remove_dict, "collections")

    if "enum_types" in remove and isinstance(
        remove_enum_types_dict := remove["enum_types"], dict
    ):
        result += handle_remove_enum_types(
            remove_enum_types_dict, dc_remove_dict["enum_types"]
        )
        remove_empty(dc_remove_dict, "enum_types")

    if "_meta" in remove and isinstance(
        remove_meta_attributes_list := remove["_meta"], list
    ):
        result += handle_remove_meta_attributes(
            remove_meta_attributes_list, dc_remove_dict["_meta"]
        )
        remove_empty(dc_remove_dict, "_meta")
    return result


def handle_remove_tree(
    remove_tree_dict: dict[str, Any],
    dc_remove_tree_dict: dict[str, Any],
) -> str:
    result = ""
    for collection_name, collection_data in remove_tree_dict.items():
        for key, data in collection_data[1].items():
            match key:
                case "fields":
                    for field_name in data[0]:
                        result += AlterSchemaHelper.get_drop_column_statement(
                            collection_name, field_name
                        )
                        dc_remove_tree_dict[collection_name][1]["fields"][0].remove(
                            field_name
                        )
                    for field_name, attrs in data[1].items():
                        for attr in attrs[0]:
                            match attr:
                                case "default":
                                    result += AlterSchemaHelper.get_drop_column_attribute_statement(
                                        collection_name, field_name, "DEFAULT"
                                    )
                                case "required":
                                    result += AlterSchemaHelper.get_drop_column_attribute_statement(
                                        collection_name, field_name, "NOT NULL"
                                    )
                                case "minimum" | "maximum" | "minLength" | "unique":
                                    constraint_name_func = getattr(
                                        HelperGetNames,
                                        f"get_{attr.lower()}_constraint_name",
                                    )
                                    constraint_name = constraint_name_func(
                                        collection_name,
                                        (
                                            [field_name]
                                            if attr == "unique"
                                            else field_name
                                        ),
                                    )
                                    result += AlterSchemaHelper.get_drop_table_constraint_statement(
                                        collection_name, constraint_name
                                    )
                                case "sql":
                                    result += AlterSchemaHelper.get_drop_view_statement(
                                        collection_name
                                    )
                                case "constant":
                                    result += AlterSchemaHelper.get_drop_trigger_statement(
                                        collection_name,
                                        HelperGetNames.get_constant_field_trigger_name(
                                            collection_name, field_name
                                        ),
                                    )
                                case value if (
                                    value in FieldAttributes.skipped_in_schema
                                ):
                                    pass
                                case "type":
                                    raise BadCodingException(
                                        f"{collection_name}/{field_name}: '{attr}' is a required field attribute."
                                    )
                                case _:
                                    # Skipped as not likely to be removed in the foreseeable future:
                                    # "to" and "reference": can only be removed if type changes to not relational field
                                    # "sequence_scope": would turn a sequence field into a regular number field
                                    raise NotImplementedError(
                                        f"{collection_name}/{field_name}: {attr}"
                                    )
                            dc_remove_tree_dict[collection_name][1]["fields"][1][
                                field_name
                            ][0].remove(attr)
                            remove_empty(
                                dc_remove_tree_dict[collection_name][1]["fields"][1],
                                field_name,
                            )
                        for attr, attr_data in attrs[1].items():
                            match attr:
                                case "log_triggers":
                                    processed_tables: dict[str, int] = {}
                                    for log_trigger in attr_data:
                                        trigger_name_iu, trigger_name_ud, *_ = (
                                            Helper.get_log_calculated_id_array_trigger_data(
                                                collection_name,
                                                field_name,
                                                log_trigger,
                                                processed_tables,
                                            )
                                        )
                                        for trigger_name in [
                                            trigger_name_iu,
                                            trigger_name_ud,
                                        ]:
                                            result += AlterSchemaHelper.get_drop_trigger_statement(
                                                log_trigger["on_table"], trigger_name
                                            )
                                # case "equal_fields":
                                #     pass
                                #     TODO: correctly handle deleted equal_fields
                                case _:
                                    raise NotImplementedError(
                                        f"{collection_name}/{field_name}: {attr}"
                                    )
                            dc_remove_tree_dict[collection_name][1]["fields"][1][
                                field_name
                            ][1].pop(attr)
                            remove_empty(
                                dc_remove_tree_dict[collection_name][1]["fields"][1],
                                field_name,
                            )
                    remove_empty(dc_remove_tree_dict[collection_name][1], "fields")
                    remove_empty(dc_remove_tree_dict, collection_name)
                case "unique_together":
                    for fields in data:
                        result += AlterSchemaHelper.get_drop_table_constraint_statement(
                            collection_name,
                            HelperGetNames.get_unique_constraint_name(
                                collection_name,
                                Helper.split_unique_together_fields(fields),
                            ),
                        )
                        dc_remove_tree_dict[collection_name][1][
                            "unique_together"
                        ].remove(fields)
                        remove_empty(
                            dc_remove_tree_dict[collection_name][1],
                            "unique_together",
                        )
                    remove_empty(dc_remove_tree_dict, collection_name)
    return result


def handle_remove_enum_types(
    remove_tree_dict: EnumTypesRemoveDict,
    dc_remove_tree_dict: EnumTypesRemoveDict,
) -> str:
    result = ""
    for collection_name, field_names in remove_tree_dict.items():
        for field_name in field_names:
            result += AlterSchemaHelper.get_drop_enum_type_statement_from_collection_and_column(
                collection_name, field_name
            )
            dc_remove_tree_dict[collection_name].remove(field_name)
        remove_empty(dc_remove_tree_dict, collection_name)
    return result


def handle_remove_meta_attributes(
    remove_meta_attributes_list: MetaAttributesRemoveList,
    dc_remove_meta_attributes_list: MetaAttributesRemoveList,
) -> str:
    result = ""
    if isinstance(remove_meta_attributes_list[1], dict) and isinstance(
        dc_remove_meta_attributes_list[1], dict
    ):
        for attr, data in remove_meta_attributes_list[1].items():
            match attr:
                case "enum_definitions":
                    for enum in data[0]:
                        result += AlterSchemaHelper.get_drop_type_statement(
                            HelperGetNames.get_enum_name(enum)
                        )
                        dc_remove_meta_attributes_list[1][attr][0].remove(enum)
                case _:
                    raise NotImplementedError(f"_meta attribute: {attr}")
            remove_empty(dc_remove_meta_attributes_list[1], attr)
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
