import os
import sys
from argparse import ArgumentParser
from copy import deepcopy
from typing import Any

from meta.dev.src.generate_sql_schema import Helper
from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.yaml_diff_generator import dumpjson, generate_diff


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--dumpjson", action="store_true")
    args = parser.parse_args()

    diff = generate_diff()
    diff_control: dict[str, Any] = deepcopy(diff)
    if args.dumpjson:
        dumpjson(diff)

    sql = ""
    # TODO create generate diff content functions in schema generator.
    add = diff["add"]
    if isinstance(add, tuple) and isinstance(add[0], dict):
        # TODO write table creation here
        pass
    if isinstance(add, tuple) and isinstance(add_tree_dict := add[1], dict):
        # This if is just for pleasing mypy
        sql += handle_add_tree(add_tree_dict, diff_control["add"][1])
    edit = diff["edit"]
    if isinstance(edit, tuple) and isinstance(edit_dict := edit[1], dict):
        sql += handle_edit_tree(edit_dict, diff_control["edit"][1])

    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data",
            "0101",
            "schema_diff.sql",
        ),
        "w",
    ) as f:
        f.write(sql)

    for dict_name in diff:
        remove_empty(diff_control, dict_name)
    # assert not diff, f"Diff control still contains:\n{diff}"
    if diff_control:
        print(f"Diff control still contains:\n{diff_control}")
        return 1
    return 0


def remove_empty(dictionary: dict[str, tuple], key: str) -> None:
    if not any(dictionary[key]):
        del dictionary[key]


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
            case "default":
                constraints_sql += Helper.get_inline_default_constraint(
                    table_name, field_name, value
                )
                del diff_control_part["default"]
            case "description":
                del diff_control_part["description"]
                # TODO this needs to be removed as this is only used for development example code
                constraints_sql += Helper.get_inline_default_constraint(
                    table_name, field_name, value
                )
    return constraints_sql


def handle_add_tree(
    add_tree_dict: dict[str, tuple[dict[str, Any], dict[str, Any]]],
    dc_add_tree_dict: dict[str, tuple[dict[str, Any], dict[str, Any]]],
) -> str:
    sql = ""
    for collection_name, collection_def in add_tree_dict.items():
        table_name = HelperGetNames.get_table_name(collection_name)
        for fields_idx in [0, 1]:
            fields = collection_def[1]["fields"][fields_idx]
            dc_fields = dc_add_tree_dict[collection_name][1]["fields"][fields_idx]
            for field_name, field_def in fields.items():
                if fields_idx == 0:
                    # field added
                    constraints_sql = generate_constraints_sql(
                        table_name, field_name, field_def, dc_fields[field_name]
                    )
                else:
                    # field altered
                    # TODO This needs ALTER COLUMN instead
                    constraints_sql = generate_constraints_sql(
                        table_name, field_name, field_def[0], dc_fields[field_name][0]
                    )
                sql += f"ALTER TABLE {table_name} ADD COLUMN {field_name}{constraints_sql};\n"
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
        for field_name, field_def in collection_def[1]["fields"][1].items():
            for constraint, value in field_def[0].items():
                constraint_name = HelperGetNames.get_default_constraint_name(
                    table_name, field_name
                )
                default_constraint = Helper.get_inline_default_constraint(
                    table_name, field_name, value
                )
                sql += f"ALTER TABLE {table_name} ALTER COLUMN {field_name} DROP CONSTRAINT {constraint_name};\n"
                sql += f"ALTER TABLE {table_name} ALTER COLUMN {field_name} ADD{default_constraint};\n"
                del dc_edit_tree_dict[collection_name][1]["fields"][1][field_name][0][
                    constraint
                ]
            remove_empty(dc_edit_tree_dict[collection_name][1]["fields"][1], field_name)
        remove_empty(dc_edit_tree_dict[collection_name][1], "fields")
        remove_empty(dc_edit_tree_dict, collection_name)
    return sql


if __name__ == "__main__":
    sys.exit(main())
