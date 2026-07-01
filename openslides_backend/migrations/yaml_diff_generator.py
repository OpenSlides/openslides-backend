import os
import sys
from argparse import ArgumentParser
from typing import Any

import simplejson as json
import yaml

from meta.dev.src.helper_get_names import ROOT, build_models_yaml_content

# renames can only happen in the leaves
# for multi layered renames it will have to have that many migrations
# Maybe future versions of this will allow multi layered renames including other changes within
# TODO pull this from the last migration module instead
renames = {
    "organization": "chaos",
    "meeting": {"fields": {"motions_number_type": "motions_assignments_number_type"}},
}

"""
To use this script create a folder 'previous_models' next to it and copy the unchanged model diffinitions from the meta into it.
It will generate the diff comparing it to the changes made to the model definitions present in the meta.
The json diff will be written to 'previous_models/diff.json' if --dumpjson is given as an argument.
"""
PREVIOUS_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "previous_models"
)


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
    curr_models = load_models(ROOT)

    validate_renames(prev_models, curr_models, renames)

    return {
        "rename": renames,
        "remove": create_remove_recursive(prev_models, curr_models, renames),
        "add": create_add_recursive(prev_models, curr_models, renames),
        "edit": create_edit_recursive(prev_models, curr_models, renames),
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
        if key in prev_models:
            if not isinstance(curr_value, dict) and curr_value != prev_models[key]:
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
