import os
import sys
from argparse import ArgumentParser
from typing import Any

import simplejson as json
import yaml

from meta.dev.src.generate_sql_schema import Helper
from meta.dev.src.helper_get_names import (
    ROOT,
    HelperGetNames,
    build_models_yaml_content,
)

# TODO move this to migration module
# renames can only happen in the leaves
# for multi layered renames it will have to have that many migrations
# Maybe future versions of this will allow multi layered renames including other changes within
renames = {
    "organization": "chaos",
    "meeting": {"fields": {"motions_number_type": "motions_assignments_number_type"}},
}


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--dumpjson", action="store_true")
    args = parser.parse_args()

    prev_models = load_models(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "0100")
    )
    curr_models = load_models(ROOT)

    # leaf_names = []
    # def collect_leaf_names(curr_models):
    #     for key, curr_value in curr_models.items():
    #         if isinstance(curr_value, dict):
    #             collect_leaf_names(curr_value)
    #         else:
    #             if key not in leaf_names:
    #                 leaf_names.append(key)
    # collect_leaf_names(curr_models)
    # print(leaf_names)

    validate_renames(prev_models, curr_models, renames)
    diff = {
        "rename": renames,
        "remove": create_remove_recursive(prev_models, curr_models, renames),
        "add": create_add_recursive(prev_models, curr_models, renames),
        "edit": create_edit_recursive(prev_models, curr_models, renames),
    }

    def deep_copy(diff: Any) -> Any:
        if isinstance(diff, dict):
            return {k: deep_copy(v) for k, v in diff.items()}
        elif isinstance(diff, list):
            return [deep_copy(item) for item in diff]
        elif isinstance(diff, tuple):
            return tuple(deep_copy(item) for item in diff)
        else:
            return diff

    diff_control = deep_copy(diff)

    if args.dumpjson:
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data",
                "0101",
                "diff.out.json",
            ),
            "w",
        ) as f:
            f.write(json.dumps(diff, indent=4))

    def generate_constraints_sql(field_def: dict[str, Any]) -> str:
        constraints_sql = ""
        for constraint, value in field_def.items():
            """
            TODO other constraints type etc
            This is a full list of leaf types we have. Including _meta.
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

    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data",
            "0101",
            "schema_diff.sql",
        ),
        "w",
    ) as f:
        # TODO create generate diff content functions in schema generator.
        for collection_name, collection_def in diff["add"][1].items():
            table_name = HelperGetNames.get_table_name(collection_name)
            for field_name, field_def in collection_def[1]["fields"][0].items():
                diff_control_part = diff_control["add"][1][collection_name][1][
                    "fields"
                ][0][field_name]
                sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name}{generate_constraints_sql(field_def)};\n"
                f.write(sql)
                if not any(
                    diff_control["add"][1][collection_name][1]["fields"][0][field_name]
                ):
                    del diff_control["add"][1][collection_name][1]["fields"][0][
                        field_name
                    ]
            for field_name, field_def in collection_def[1]["fields"][1].items():
                diff_control_part = diff_control["add"][1][collection_name][1][
                    "fields"
                ][1][field_name][0]
                sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name}{generate_constraints_sql(field_def[0])};\n"
                f.write(sql)
                if not any(
                    diff_control["add"][1][collection_name][1]["fields"][1][field_name]
                ):
                    del diff_control["add"][1][collection_name][1]["fields"][1][
                        field_name
                    ]
            if not any(diff_control["add"][1][collection_name][1]["fields"]):
                del diff_control["add"][1][collection_name][1]["fields"]
            if not any(diff_control["add"][1][collection_name]):
                del diff_control["add"][1][collection_name]
        for collection_name, collection_def in diff["edit"][1].items():
            table_name = HelperGetNames.get_table_name(collection_name)
            for field_name, field_def in collection_def[1]["fields"][1].items():
                for constraint, value in field_def[0].items():
                    sql = f"ALTER TABLE {table_name} ALTER COLUMN {field_name} DROP CONSTRAINT {HelperGetNames.get_default_constraint_name(table_name, field_name)};\n"
                    sql += f"ALTER TABLE {table_name} ALTER COLUMN {field_name} ADD{Helper.get_inline_default_constraint(table_name, field_name, value)};\n"
                    del diff_control["edit"][1][collection_name][1]["fields"][1][
                        field_name
                    ][0][constraint]
                f.write(sql)
                if not any(
                    diff_control["edit"][1][collection_name][1]["fields"][1][field_name]
                ):
                    del diff_control["edit"][1][collection_name][1]["fields"][1][
                        field_name
                    ]
            if not any(diff_control["edit"][1][collection_name][1]["fields"]):
                del diff_control["edit"][1][collection_name][1]["fields"]
            if not any(diff_control["edit"][1][collection_name]):
                del diff_control["edit"][1][collection_name]

    for dict_name in ["rename", "remove", "add", "edit"]:
        if not any(diff_control[dict_name]):
            del diff_control[dict_name]
    # assert not diff, f"Diff control still contains:\n{diff}"
    if diff_control:
        print(f"Diff control still contains:\n{diff_control}")
        return 1
    return 0


def validate_renames(
    prev_models: dict[str, Any],
    curr_models: dict[str, Any],
    renames_dict: dict[str, Any],
) -> None:
    for key, rena_value in renames_dict.items():
        if isinstance(rena_value, dict):
            validate_renames(prev_models[key], curr_models[key], rena_value)
        elif key not in prev_models:
            raise Exception(
                f"Faulty renames or collection yml files. {key} not in old yml files."
            )
        elif rena_value not in curr_models:
            raise Exception(
                f"Faulty renames or collection yml files. {rena_value} not in new yml files."
            )
        elif rena_value in prev_models:
            raise Exception(
                f"Faulty renames or collection yml files. {rena_value} already existed in old yml files."
            )
        elif key in curr_models:
            raise Exception(
                f"Faulty renames or collection yml files. {key} already existed in new yml files."
            )


def create_remove_recursive(
    prev_models: dict[str, Any],
    curr_models: dict[str, Any],
    renames_dict: dict[str, Any],
) -> list[list[str] | dict[str, Any]] | None:
    missing_entries = []
    tree = {}
    for key, prev_value in prev_models.items():
        if isinstance(renames_dict.get(key), str):
            print(key + " renamed -> skip for remove")
            continue
        if key not in curr_models:
            missing_entries.append(key)
        elif isinstance(prev_value, dict):
            result = create_remove_recursive(
                prev_value, curr_models[key], renames_dict.get(key, {})
            )
            if result is not None:
                tree[key] = result

    if missing_entries or tree:
        return [missing_entries, tree]
    else:
        return None


def create_add_recursive(
    prev_models: dict[str, Any],
    curr_models: dict[str, Any],
    renames_dict: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """
    Returns the additional entries on pos 0 and the sub trees on pos 1.
    """
    additional_entries = {}
    tree = {}
    for key, curr_value in curr_models.items():
        if key in list(renames_dict.values()):
            print(key + " renamed -> skip for add")
            continue
        if key not in prev_models:
            additional_entries[key] = curr_models[key]
        elif isinstance(curr_value, dict):
            result = create_add_recursive(
                prev_models[key], curr_value, renames_dict.get(key, {})
            )
            if result is not None:
                tree[key] = result
    if additional_entries or tree:
        return (additional_entries, tree)
    else:
        return None


def create_edit_recursive(
    prev_models: dict[str, Any],
    curr_models: dict[str, Any],
    renames_dict: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """
    Returns the edited entries on pos 0 and the sub trees on pos 1.
    TODO This has a very similar structure to the add recursive function. Maybe combine with use of lambda or passing additional dict.
    TODO This should only generate diffs for the leafs. Thus the structure should be reconsidered. Maybe flatter or integrating rename info.
    """
    edited_entries = {}
    tree = {}
    for key, curr_value in curr_models.items():
        if key in list(renames_dict.values()):
            print(key + " renamed -> skip for edit")
            continue
        if key not in prev_models:
            pass
        elif not isinstance(curr_value, dict) and curr_value != prev_models[key]:
            edited_entries[key] = curr_models[key]
        elif isinstance(curr_value, dict):
            result = create_edit_recursive(
                prev_models[key], curr_value, renames_dict.get(key, {})
            )
            if result is not None:
                tree[key] = result
    if edited_entries or tree:
        return (edited_entries, tree)
    else:
        return None


def load_models(mig_data_path: str) -> dict[str, Any]:
    meta_file = os.path.join(mig_data_path, "collection-meta.yml")
    collections_dir = os.path.join(mig_data_path, "collections")
    return yaml.safe_load(build_models_yaml_content(meta_file, collections_dir))


if __name__ == "__main__":
    sys.exit(main())
