import os
import sys
from argparse import ArgumentParser
from typing import Any, TypedDict

import simplejson as json
import yaml
from typing_extensions import NotRequired

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
Renames = tuple[dict[str, str], dict[str, dict[str, str]]]
CollectionsRemoveList = list[list[str] | dict[str, Any]]
EnumTypesRemoveDict = dict[str, list[str]]
MetaAttributesRemoveList = list[list[str] | dict[str, Any]]
PREVIOUS_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "previous_models"
)


class RemoveDiffDict(TypedDict):
    collections: NotRequired[CollectionsRemoveList]
    enum_types: NotRequired[EnumTypesRemoveDict]
    _meta: NotRequired[MetaAttributesRemoveList]


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


def load_models(mig_data_path: str) -> dict[str, Any]:
    meta_file = os.path.join(mig_data_path, "collection-meta.yml")
    collections_dir = os.path.join(mig_data_path, "collections")
    return yaml.safe_load(build_models_yaml_content(meta_file, collections_dir))


def check_renames_node(renames: dict[str, str], collection_name: str | None) -> None:
    if collection_name:
        prev_tree = PREV_MODELS[collection_name]["fields"]
        curr_tree = CURR_MODELS[collection_name]["fields"]
        s = ""
    else:
        prev_tree = PREV_MODELS
        curr_tree = CURR_MODELS
        collection_name = "collection"
        s = "s"
    err_msg_base = f"Faulty {collection_name} yml file{s}. "
    for name_old, name_new in renames.items():
        if name_old not in prev_tree:
            raise Exception(f"{err_msg_base}{name_old} not in old yml file{s}.")
        elif name_new not in curr_tree:
            raise Exception(f"{err_msg_base}{name_new} not in new yml file{s}.")
        elif name_new in prev_tree:
            raise Exception(
                f"{err_msg_base}{name_new} already existed in old yml file{s}."
            )
        elif name_old in curr_tree:
            raise Exception(
                f"{err_msg_base}{name_old} still exists in new yml file{s}."
            )


def validate_renames(renames: Renames) -> None:
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
    # Edits caused by adding or removing field attributes
    secondary_edits: dict[str, Any] = {}

    return {
        "rename": RENAMES,
        "remove": create_remove_recursive(
            PREV_MODELS, CURR_MODELS, RENAMES, secondary_edits
        ),
        "add": create_add_recursive(PREV_MODELS, CURR_MODELS, RENAMES),
        "edit": create_edit_recursive(
            PREV_MODELS, CURR_MODELS, RENAMES, secondary_edits
        ),
    }


def update_edits_tree(
    edits_tree: dict[str, Any], collection: str, field: str, attr: str, value: Any
) -> None:
    edits_tree.setdefault(collection, [{}, {}])[1].setdefault("fields", [{}, {}])[
        1
    ].setdefault(field, [{}, {}])[0][attr] = value


def create_remove_recursive(
    prev_models: dict[str, Any],
    curr_models: dict[str, Any],
    renames: Renames | dict,
    secondary_edits: dict[str, Any],
    enum_tree: EnumTypesRemoveDict = {},
    path: tuple[str, ...] = (),
) -> CollectionsRemoveList | RemoveDiffDict | None:
    """
    Parameter `path` is used only internally and describes the path to the node
    within the tree created inside the outer create_remove_recursive call.
    Example: (collection_name, "fields", field_name)
    """
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
            if key == "id" or len(path) >= 3 and path[2] == "id":
                continue
            if key in [
                *CollectionAttributes.unique_together,
                "log_triggers",
                "equal_fields",
            ]:
                # Old definitions are needed to re-build the trigger definitions names
                tree[key] = prev_value
            elif key == "maxLength":
                # Should be processed as type change
                update_edits_tree(secondary_edits, path[0], path[2], "maxLength", None)
            elif is_enum(key) and len(path) >= 3:
                # Should be processed as type change
                if "type" in curr_models:
                    update_edits_tree(
                        secondary_edits, path[0], path[2], "type", curr_models["type"]
                    )
                # Delete enum only when it is defined on the field
                if is_field_enum(prev_value):
                    enum_tree.setdefault(path[0], []).append(path[2])
            elif curr_models:
                # TODO: currently `constant` on the reading side of the relation
                # is being excluded from diff within this check. This has to be changed
                # after implementing https://github.com/OpenSlides/openslides-meta/issues/542
                if len(path) >= 2 and key != "sql":
                    if len(path) == 2:
                        field_name = key
                        field_def = prev_value
                    else:
                        field_name = path[2]
                        field_def = PREV_MODELS[path[0]][path[1]][path[2]]
                    if not (
                        "type" in field_def
                        and is_relational_field(field_def["type"])
                        and is_view_field(path[0], field_name, field_def, PREV_MODELS)
                    ):
                        missing_entries.append(key)
                else:
                    missing_entries.append(key)
        if isinstance(prev_value, dict) and key != "items":
            result = create_remove_recursive(
                prev_value,
                curr_models.get(key, {}),
                recurse_renames.get(key, {}),
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
            return None

    combined_result: RemoveDiffDict = {}
    if _meta := tree.pop("_meta", None):
        combined_result["_meta"] = _meta
    if missing_entries or tree:
        combined_result["collections"] = [missing_entries, tree]
    if enum_tree:
        combined_result["enum_types"] = enum_tree

    if combined_result:
        return combined_result
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
    secondary_edits: dict[str, Any] = {},
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """
    Returns the edited entries on pos 0 and the sub trees on pos 1.
    TODO This has a very similar structure to the add recursive function. Maybe combine with use of lambda or passing additional dict.
    TODO This should only generate diffs for the leafs. Thus the structure should be reconsidered. Maybe flatter or integrating rename info.
    TODO: changes in lists for `unique_together`, `unique_together_strict` and `log_triggers` must be processed as add or remove operations.
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
    if secondary_edits:
        for collection, collection_data in secondary_edits.items():
            for field_name, field_data in collection_data[1]["fields"][1].items():
                for attr, value in field_data[0].items():
                    update_edits_tree(tree, collection, field_name, attr, value)
    if edited_entries or tree:
        return (edited_entries, tree)
    else:
        return None


def is_enum(key: str) -> bool:
    return key in FieldAttributes.enum_definitions


def is_field_enum(value: Any) -> bool:
    """Checks that enum options are defined directly on the field"""
    return isinstance(value, list) or (
        isinstance(value, dict) and isinstance(value["enum"], list)
    )


def is_relational_field(field_type: str) -> bool:
    return field_type in [
        "relation",
        "generic-relation",
        "relation-list",
        "generic-relation-list",
    ]


def is_view_field(
    collection_name: str,
    field_name: str,
    field_data: dict[str, Any],
    all_prev_models: dict[str, dict[str, Any]],
) -> bool:
    own = TableFieldType(collection_name, field_name, field_data)

    new_models = InternalHelper.MODELS
    InternalHelper.MODELS = all_prev_models
    foreign_fields = InternalHelper.get_definitions_from_foreign_list(
        field_data.get("to", None),
        field_data.get("reference", None),
    )
    InternalHelper.MODELS = new_models

    state, *_ = InternalHelper.check_relation_definitions(own, foreign_fields)
    return state == FieldSqlErrorType.SQL


if __name__ == "__main__":
    sys.exit(main())
