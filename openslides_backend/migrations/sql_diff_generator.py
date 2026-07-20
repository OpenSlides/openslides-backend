import os
import sys
from argparse import ArgumentParser
from copy import deepcopy
from typing import Any, cast

import simplejson as json

from meta.dev.src.generate_sql_schema import GenerateCodeBlocks, Helper
from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.yaml_diff_generator import dumpjson, generate_diff

"""
This script works in conjunction with the yaml_diff_generator.py.
To use this script create a folder 'previous_models' next to it and copy the unchanged model diffinitions from the meta into it.
It will generate the sql diff comparing it to the changes made to the model definitions present in the meta.
The sql diff will be written to 'migrations/mig_[last migration number].*/schema_diff.sql'.
"""


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
            sql += f"DROP TABLE {collection_name}_t CASCADE;\n"
            diff_control["remove"][0].remove(collection_name)
    if isinstance(remove, list) and isinstance(remove_tree_dict := remove[1], dict):
        sql += handle_remove_tree(remove_tree_dict, diff_control["remove"][1])

    sql += "\n-- RENAME SECTION --\n"
    rename = diff["rename"]
    if isinstance(rename, dict):
        sql += handle_rename(rename, diff_control["rename"])

    sql += "\n-- ADD SECTION --\n"
    add = diff["add"]
    GenerateCodeBlocks.generate_the_code()
    if isinstance(add, tuple) and isinstance(add[0], dict):
        sql += generate_new_collection_sql(add[0], diff_control["add"][0])
    if isinstance(add, tuple) and isinstance(add_tree_dict := add[1], dict):
        sql += handle_add_tree(add_tree_dict, diff_control["add"][1])

    sql += "\n-- EDIT SECTION --\n"
    edit = diff["edit"]
    if isinstance(edit, tuple) and isinstance(edit_dict := edit[1], dict):
        sql += handle_edit_tree(edit_dict, diff_control["edit"][1])

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
        sql += GenerateCodeBlocks.view_sql[collection_name]
    for collection_name in add:
        found.add(collection_name)
        sql += GenerateCodeBlocks.alter_table_final_sql[collection_name]
    for collection_name in add:
        found.add(collection_name)
        sql += GenerateCodeBlocks.trigger_sql[collection_name]
    for collection_name in add:
        found.add(collection_name)
        sql += GenerateCodeBlocks.intermediate_sql[collection_name]
    for collection_name in found:
        del dc_add[collection_name]
    return sql


def generate_constraints_sql(
    table_name: str,
    field_name: str,
    field_def: dict[str, Any],
    diff_control_part: dict[str, Any],
) -> str:
    constraints_sql = ""
    for constraint, value in field_def.items():
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
        deferred
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
            case "to":
                # TODO
                pass
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
        del diff_control_part[constraint]
    return constraints_sql


def generate_altered_constraints_sql(
    table_name: str,
    field_name: str,
    field_def: dict[str, Any],
    diff_control_part: tuple[dict[str, Any], dict[str, Any]],
) -> str:
    constraints_sql = ""
    for constraint, value in field_def.items():
        match constraint:
            case "default":
                constraints_sql += f"ALTER TABLE {table_name} ALTER COLUMN {field_name} SET DEFAULT {field_def['default']};\n"
            case "description":
                pass
            case "reference" | "to":
                # TODO this can be better about rename, maybe pass or store centrally
                directory = MigrationHelper.get_last_migration_directory()
                renames = MigrationHelper.get_migration_class(directory).renames
                if table_name in renames or field_name in renames.get(
                    table_name, {}
                ).get("fields", {}):
                    continue
                else:
                    NotImplementedError(
                        f"{constraint}: {value} is probably a view field or unmentioned in renames."
                    )
                # TODO
                # recreate affected triggers
                # recreate views
            case _:
                raise NotImplementedError(f"{constraint}: {value}")
        del diff_control_part[0][constraint]
    return constraints_sql


def handle_rename(
    rename: dict[str, str | dict[str, dict[str, dict[str, Any]]]],
    dc_rename_dict: dict[str, str | dict[str, dict[str, dict[str, Any]]]],
) -> str:
    result = ""
    for collection_name_old, value in rename.items():
        if isinstance(value, str):
            result += f"ALTER TABLE {collection_name_old}_t RENAME TO {value}_t;\n"
            # TODO Renaming views
            del dc_rename_dict[collection_name_old]
        else:
            dc_collection = cast(dict, dc_rename_dict[collection_name_old])
            for field_name_old, field_name_new in value["fields"].items():
                result += f"ALTER TABLE {collection_name_old}_t RENAME COLUMN {field_name_old} TO {field_name_new}_t;\n"
                del dc_collection["fields"][field_name_old]
            # TODO Renaming and redefining constraints
            remove_empty(dc_collection, "fields")
            remove_empty(dc_rename_dict, collection_name_old)
    return result


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
                    # TODO needs to differentiate cardinality and type maybe usage of CodeGenerator defined functions
                    constraints_sql = generate_constraints_sql(
                        table_name, field_name, field_def, dc_fields[field_name]
                    )
                    sql += f"ALTER TABLE {table_name} ADD COLUMN {field_name}{constraints_sql};\n"
                else:
                    # field altered
                    sql += generate_altered_constraints_sql(
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
            sql += generate_altered_constraints_sql(
                table_name, field_name, field_def[0], dc_fields[field_name]
            )
            remove_empty(dc_edit_tree_dict[collection_name][1]["fields"][1], field_name)
        remove_empty(dc_edit_tree_dict[collection_name][1], "fields")
        remove_empty(dc_edit_tree_dict, collection_name)
    return sql


if __name__ == "__main__":
    sys.exit(main())
