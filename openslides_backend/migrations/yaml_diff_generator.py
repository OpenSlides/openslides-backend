import os
import sys
from argparse import ArgumentParser
from string import Template
from typing import Any

import simplejson as json
import yaml

from meta.dev.src.helper_get_names import ROOT as CURR_MODELS_DIR
from meta.dev.src.helper_get_names import build_models_yaml_content
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
Renames = tuple[dict[str, str], dict[str, dict[str, str]]]
PREVIOUS_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "previous_models"
)


def load_models(mig_data_path: str) -> dict[str, Any]:
    meta_file = os.path.join(mig_data_path, "collection-meta.yml")
    collections_dir = os.path.join(mig_data_path, "collections")
    return yaml.safe_load(build_models_yaml_content(meta_file, collections_dir))


def check_renames_node(renames: dict[str, str], collection_name: str | None) -> None:
    if collection_name:
        prev_tree = PREV_MODELS[collection_name]["fields"]
        curr_tree = CURR_MODELS[collection_name]["fields"]
        subst_dict = {"collection": collection_name, "s": ""}
    else:
        prev_tree = PREV_MODELS
        curr_tree = CURR_MODELS
        subst_dict = {"collection": "collection", "s": "s"}
    for name_old, name_new in renames.items():
        subst_dict["name_old"] = name_old
        subst_dict["name_new"] = name_new
        if name_old not in prev_tree:
            raise Exception(
                Template(
                    "Faulty {collection} yml file{s}. {name_old} not in old yml file{s}."
                ).substitute(subst_dict)
            )
        elif name_new not in curr_tree:
            raise Exception(
                Template(
                    "Faulty {collection} yml file{s}. {name_new} not in new yml file{s}."
                ).substitute(subst_dict)
            )
        elif name_new in prev_tree:
            raise Exception(
                Template(
                    "Faulty {collection} yml file{s}. {name_new} already existed in old yml file{s}."
                ).substitute(subst_dict)
            )
        elif name_old in curr_tree:
            raise Exception(
                Template(
                    "Faulty {collection} yml file{s}. {name_old} still exists in new yml file{s}."
                ).substitute(subst_dict)
            )


def validate_renames(
    renames: Renames,
) -> None:
    collection_renames = renames[0]
    field_renames = renames[1]
    check_renames_node(collection_renames, None)
    for collection_old, value in field_renames.items():
        check_renames_node(value, collection_old)


def load_renames() -> Renames:
    directory = MigrationHelper.get_last_migration_directory()
    renames = MigrationHelper.get_migration_class(directory).renames
    validate_renames(renames)
    return renames


PREV_MODELS = load_models(PREVIOUS_MODELS_DIR)
CURR_MODELS = load_models(CURR_MODELS_DIR)
RENAMES = load_renames()


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
    return {
        "rename": RENAMES,
        "remove": create_remove_recursive(PREV_MODELS, CURR_MODELS, RENAMES),
        "add": create_add_recursive(PREV_MODELS, CURR_MODELS, RENAMES),
        "edit": create_edit_recursive(PREV_MODELS, CURR_MODELS, RENAMES),
    }


def create_remove_recursive(
    prev_models: dict[str, Any],
    curr_models: dict[str, Any],
    renames: Renames | dict,
) -> list[list[str] | dict[str, Any]] | None:
    missing_entries = []
    tree = {}
    if isinstance(renames, tuple):
        renames_dict = renames[0]
        recurse_renames = {"fields": renames[1]}
    else:
        renames_dict = renames
        recurse_renames = renames

    for key, prev_value in prev_models.items():
        if isinstance(renames_dict.get(key), str):
            print(key + " renamed -> skip for remove")
            continue
        if key not in curr_models:
            missing_entries.append(key)
        elif isinstance(prev_value, dict):
            result = create_remove_recursive(
                prev_value, curr_models[key], recurse_renames.get(key, {})
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
    renames: Renames | dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """
    Returns the additional entries on pos 0 and the sub trees on pos 1.
    """
    additional_entries = {}
    tree = {}
    if isinstance(renames, tuple):
        renames_dict = renames[0]
    else:
        renames_dict = renames

    new_names = {v: k for k, v in renames_dict.items() if isinstance(v, str)}
    for key, curr_value in curr_models.items():
        if key in new_names:
            print(f"{new_names[key]} renamed to {key} -> skip for add")
            continue
        if key not in prev_models:
            additional_entries[key] = curr_models[key]
        elif isinstance(curr_value, dict):
            if isinstance(renames, tuple):
                recurse_renames = {"fields": renames[1].get(key, {})}
            else:
                recurse_renames = renames.get(key, {})
            result = create_add_recursive(prev_models[key], curr_value, recurse_renames)
            if result is not None:
                tree[key] = result
    if additional_entries or tree:
        return (additional_entries, tree)
    else:
        return None


def create_edit_recursive(
    prev_models: dict[str, Any],
    curr_models: dict[str, Any],
    renames: Renames | dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """
    Returns the edited entries on pos 0 and the sub trees on pos 1.
    TODO This has a very similar structure to the add recursive function. Maybe combine with use of lambda or passing additional dict.
    TODO This should only generate diffs for the leafs. Thus the structure should be reconsidered. Maybe flatter or integrating rename info.
    """
    edited_entries = {}
    tree = {}
    if isinstance(renames, tuple):
        renames_dict = renames[0]
    else:
        renames_dict = renames

    new_names = {v: k for k, v in renames_dict.items() if isinstance(v, str)}
    for key, curr_value in curr_models.items():
        if key in new_names:
            print(f"{new_names[key]} renamed to {key} -> skip for edit")
            continue
        if key in prev_models:
            if not isinstance(curr_value, dict) and curr_value != prev_models[key]:
                edited_entries[key] = curr_models[key]
            elif isinstance(curr_value, dict):
                if isinstance(renames, tuple):
                    recurse_renames = {"fields": renames[1].get(key, {})}
                else:
                    recurse_renames = renames.get(key, {})
                result = create_edit_recursive(
                    prev_models[key], curr_value, recurse_renames
                )
                if result is not None:
                    tree[key] = result
    if edited_entries or tree:
        return (edited_entries, tree)
    else:
        return None


if __name__ == "__main__":
    sys.exit(main())
