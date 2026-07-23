import os
import sys
from argparse import ArgumentParser
from typing import Any

import simplejson as json
import yaml

from meta.dev.src.helper_get_names import ROOT as CURR_MODELS_DIR
from meta.dev.src.helper_get_names import (
    FieldSqlErrorType,
    InternalHelper,
    TableFieldType,
    build_models_yaml_content,
)
from openslides_backend.migrations.migration_helper import MigrationHelper

"""
To use this script create a folder 'previous_models' next to it and copy the unchanged model diffinitions from the meta into it.
It will generate the diff comparing it to the changes made to the model definitions present in the meta.
The json diff will be written to 'previous_models/diff.json' if --dumpjson is given as an argument.
# edits can only happen in the yaml file leaves
# renames can only happen in the diffs leaves
# for multi layered renames it will have to have that many migrations
# Maybe future versions of this will allow multi layered renames including other changes within
"""
PREVIOUS_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "previous_models"
)


class FieldAttributes:
    skipped_in_schema = [
        "calculated",
        "constant_legacy",
        "deferred",
        "description",
        "on_delete",
        "restriction_mode",
    ]
    field_attributes = [
        "default",
        "maxLength",
        "maximum",
        "minLength",
        "minimum",
        "required",
        "type",
        "unique",
    ]
    relational_field_attributes = [
        "reference",
        "to",
    ]
    view_attributes = [
        "sql",
    ]
    trigger_definitions = [
        "constant",
        "equal_fields",
        "log_triggers",
        "read_only",
        "sequence_scope",
    ]
    enum_definitions = [
        "enum",
        "items",
    ]
    used_in_schema = [
        *field_attributes,
        *relational_field_attributes,
        *view_attributes,
        *trigger_definitions,
        *enum_definitions,
    ]


class CollectionAttributes:
    unique_together = [
        "unique_together",
        "unique_together_strict",
    ]


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--dumpjson", action="store_true")
    args = parser.parse_args()
    diff = generate_diff()
    if args.dumpjson:
        dumpjson(diff)
    return 0


def dumpjson(diff: dict[str, Any]) -> None:
    with open(os.path.join(PREVIOUS_MODELS_DIR, "diff.json"), "w") as f:
        f.write(json.dumps(diff, indent=4))


def generate_diff() -> dict[str, Any]:
    prev_models = load_models(PREVIOUS_MODELS_DIR)
    curr_models = load_models(CURR_MODELS_DIR)
    directory = MigrationHelper.get_last_migration_directory()
    renames = MigrationHelper.get_migration_class(directory).renames

    validate_renames(prev_models, curr_models, renames)
    secondary_edits = {}

    return {
        "rename": renames,
        "remove": create_remove_recursive(
            prev_models, curr_models, renames, prev_models, secondary_edits
        ),
        "add": create_add_recursive(prev_models, curr_models, renames),
        "edit": create_edit_recursive(
            prev_models, curr_models, renames, secondary_edits
        ),
    }


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


def update_edits_tree(tree, collection, field, attr, value):
    tree.setdefault(collection, [{}, {}])[1].setdefault("fields", [{}, {}])[
        1
    ].setdefault(field, [{}, {}])[0][attr] = value


def create_remove_recursive(
    prev_models: dict[str, Any],
    curr_models: dict[str, Any],
    renames_dict: dict[str, Any],
    all_prev_models: dict[str, Any],
    secondary_edits: dict[str, Any] = {},
    enum_tree: dict[str, list[str]] = {},
    path: tuple[str, ...] = (),
) -> (
    list[list[str] | dict[str, Any]]
    | dict[str, list[list[str] | dict[str, Any]] | dict[str, str]]
    | None
):
    missing_entries = []
    tree = {}
    for key, prev_value in prev_models.items():
        if isinstance(renames_dict.get(key), str):
            print(key + " renamed -> skip for remove")
            continue
        if key not in curr_models:
            if key in CollectionAttributes.unique_together:
                tree[key] = prev_value
                continue
            if curr_models:
                if len(path) == 2 and prev_value["type"] in [
                    "relation",
                    "generic-relation",
                    "relation-list",
                    "generic-relation-list",
                ]:
                    own = TableFieldType(path[0], key, prev_value)

                    new_models = InternalHelper.MODELS
                    InternalHelper.MODELS = all_prev_models
                    foreign_fields = InternalHelper.get_definitions_from_foreign_list(
                        prev_value.get("to", None),
                        prev_value.get("reference", None),
                    )
                    InternalHelper.MODELS = new_models

                    state, _, _, _ = InternalHelper.check_relation_definitions(
                        own, foreign_fields
                    )
                    is_view_field = state == FieldSqlErrorType.SQL
                    if not is_view_field:
                        missing_entries.append(key)
                else:
                    missing_entries.append(key)
            elif key in FieldAttributes.enum_definitions and (
                isinstance(prev_value, list)
                or (
                    isinstance(prev_value, dict)
                    and isinstance(prev_value["enum"], list)
                )
            ):
                if len(path) >= 3:
                    model = path[0]
                    field = path[2]
                    enum_tree.setdefault(model, []).append(field)
                    if "type" in curr_models:
                        update_edits_tree(
                            secondary_edits, model, field, "type", curr_models["type"]
                        )
        if isinstance(prev_value, dict) and key != "items":
            result = create_remove_recursive(
                prev_value,
                curr_models.get(key, {}),
                renames_dict.get(key, {}),
                all_prev_models,
                secondary_edits,
                enum_tree,
                path + (key,),
            )
            if result is not None:
                tree[key] = result

    if path:
        if missing_entries or tree:
            return [missing_entries, tree]
    else:
        return {
            "collections": [missing_entries, tree],
            "enum_types": enum_tree,
        }

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
    secondary_edits: dict[str, Any] = {},
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """
    Returns the edited entries on pos 0 and the sub trees on pos 1.
    TODO This has a very similar structure to the add recursive function. Maybe combine with use of lambda or passing additional dict.
    TODO This should only generate diffs for the leafs. Thus the structure should be reconsidered. Maybe flatter or integrating rename info.
    TODO: if list of unique_together and unique_together_strict changes, the changes get added to the diff here, even when we don't change an existing item but add or remove.
    """
    edited_entries = {}
    tree = {}
    for key, curr_value in curr_models.items():
        if key in list(renames_dict.values()):
            print(key + " renamed -> skip for edit")
            continue
        if key in prev_models:
            if not isinstance(curr_value, dict) and curr_value != prev_models[key]:
                edited_entries[key] = curr_models[key]
            elif isinstance(curr_value, dict):
                result = create_edit_recursive(
                    prev_models[key], curr_value, renames_dict.get(key, {})
                )
                if result is not None:
                    tree[key] = result
    if secondary_edits:
        for collection, collection_data in secondary_edits.items():
            for field_name, field_data in collection_data[1]["fields"][1].items():
                for attr, value in field_data[0].items():
                    update_edits_tree(tree, collection, field_name, attr, value)
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
