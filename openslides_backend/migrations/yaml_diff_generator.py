from meta.dev.src.helper_get_names import (
    DEFAULT_COLLECTION_META,
    FieldSqlErrorType,
    HelperGetNames,
    InternalHelper,
    TableFieldType,
)
from typing import Any
from meta.dev.src.helper_get_names import build_models_yaml_content, ROOT
import os
import simplejson as json
import sys
import yaml

# TODO move this to migration module
# renames can only happen in the leaves
# for multi layered renames it will have to have that many migrations
# Maybe future versions of this will allow multi layered renames including other changes within
renames = {
    "organization": "chaos",
    "meeting": {
        "fields": {
            "motions_number_type": "motions_assignments_number_type"
        }
    }
}

def main() -> None:
    prev_models = load_models(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "0100"))
    curr_models = load_models(ROOT)

    validate_renames(prev_models, curr_models, renames)
    diff = {
        "rename": renames, 
        "remove": create_remove_recursive(prev_models, curr_models, renames),
        "add":  create_add_recursive(prev_models, curr_models, renames)
    }

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "0101", "diff.out.json"), "w") as f:
        f.write(json.dumps(diff, indent=4))

    # with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "0101", "schema_diff.sql"), "w") as f:
    #     # TODO create generate diff content functions in schema generator. Esp. constraints as those reappear.
    #     for collection_name, collection_def in diff["add"].items():
    #         for field_name, field_def in collection_def.items():
    #             sql = f"ALTER TABLE {collection_name}_t ADD COLUMN {collection_def};"
    #             f.write(sql)

def validate_renames(prev_models: dict[str, Any], curr_models:dict[str, Any], renames_dict:dict[str, Any]) -> dict[str, Any] | None:
    for key, rena_value in renames_dict.items():
        if isinstance(rena_value, dict):
            validate_renames(prev_models[key], curr_models[key], rena_value)
        elif key not in prev_models:
            raise Exception(f"Faulty renames or collection yml files. '{key}' not in old yml files.")
        elif rena_value not in curr_models:
            raise Exception(f"Faulty renames or collection yml files. '{rena_value}' not in new yml files.")
        elif rena_value in prev_models:
            raise Exception(f"Faulty renames or collection yml files. '{rena_value}' already existed in old yml files.")
        elif key in curr_models:
            raise Exception(f"Faulty renames or collection yml files. '{key}' already existed in new yml files.")

def create_remove_recursive(prev_models: dict[str, Any], curr_models:dict[str, Any], renames_dict:dict[str, Any]) -> list[list[str], dict[str, Any]] | None:
    missing_entries = []
    tree = {}
    for key, prev_value in prev_models.items():
        if isinstance(renames_dict.get(key), str):
            print(key + " renamed -> skip for remove")
            continue
        if key not in curr_models:
            missing_entries.append(key)
        elif isinstance(prev_value, dict):
            result = create_remove_recursive(prev_value, curr_models[key], renames_dict.get(key, {}))
            if result is not None:
                tree[key] = result

    if missing_entries or tree:
        return [missing_entries, tree]
    else:
        return None

def create_add_recursive(prev_models: dict[str, Any], curr_models:dict[str, Any], renames_dict:dict[str, Any]) -> dict[str, Any] | None:
    tree = {}
    for key, curr_value in curr_models.items():
        if key in list(renames_dict.values()):
            print(key + " renamed -> skip for add")
            continue
        if key not in prev_models or not isinstance(curr_value, dict) and curr_value != prev_models[key]:
            tree[key] = curr_value
        elif isinstance(curr_value, dict):
            result = create_add_recursive(prev_models[key], curr_value, renames_dict.get(key, {}))
            if result:
                tree[key] = result
    if tree:
        return tree
    else:
        return None
    

def load_models(mig_data_path: str) -> dict[str, Any]:
    meta_file = os.path.join(mig_data_path, "collection-meta.yml")
    collections_dir = os.path.join(mig_data_path, "collections")
    return yaml.safe_load(build_models_yaml_content(meta_file, collections_dir))

if __name__ == "__main__":
    sys.exit(main())
