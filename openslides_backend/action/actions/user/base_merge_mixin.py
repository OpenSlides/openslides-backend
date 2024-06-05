from typing import Any, TypedDict

from openslides_backend.services.datastore.interface import PartialModel

from ....models.base import Model
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, CollectionField
from ...action import Action


class MergeModeDict(TypedDict, total=False):
    ignore: list[CollectionField]
    # raise exception if set on any user
    error: list[CollectionField]
    # error if all examples of the field that are set aren't the same,
    # otherwise use that value
    require_equality: list[CollectionField]
    # use highest value among users
    highest: list[CollectionField]
    # use lowest value among users
    lowest: list[CollectionField]
    # use value of highest ranking user
    priority: list[CollectionField]
    # merge the lists together, filter out duplicates
    merge: list[CollectionField]
    # merge relations normally, but detect if targets serve the same function
    # and if they do, merge them together and delete the lower-rank targets
    # should only be n:1 relations
    deep_merge: dict[CollectionField, Collection]
    # deep merge, but if the main model of the sub-merge does not belong to the
    # parent main model, a new sub-model with the merged data will be created
    deep_create_merge: dict[CollectionField, Collection]
    # field has its own function
    special_function: list[CollectionField]


class MergeUpdateOperations(TypedDict):
    create: list[dict[str, Any]]
    update: list[dict[str, Any]]
    delete: list[int]


class BaseMergeMixin(Action):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._collection_field_groups: dict[Collection, MergeModeDict] = {}
        self._all_collection_fields: dict[Collection, list[CollectionField]] = {}
        # self._collection_operations: dict[Collection, MergeOperations] = {}

    def mass_prefetch_for_merge(
        self, collection_to_ids: dict[Collection, list[int]]
    ) -> None:
        data = self.datastore.get_many(
            [
                GetManyRequest(
                    collection,
                    ids,
                    self._all_collection_fields[collection].copy(),
                )
                for collection, ids in collection_to_ids.items()
            ]
        )
        mass_prefetch_payload: dict[Collection, list[int]] = {}
        for collection, collection_data in data.items():
            if recurse := self._collection_field_groups.get(collection, {}).get(
                "deep_merge"
            ):
                for field, recurse_collection in recurse.items():
                    ids: list[int] = []
                    for date in collection_data.values():
                        if vals := date.get(field):
                            ids.extend(vals)
                    if len(ids):
                        mass_prefetch_payload[recurse_collection] = ids
        if len(mass_prefetch_payload):
            self.mass_prefetch_for_merge(mass_prefetch_payload)

    def add_collection_field_groups(
        self,
        Class: type[Model],
        # operations: MergeOperations,
        field_groups: MergeModeDict,
    ) -> None:
        """Should be called once in __init__ of every sub-class"""
        collection = Class.__dict__["collection"]
        self._collection_field_groups[collection] = field_groups
        self._all_collection_fields[collection] = [
            i
            for i in Class.__dict__.keys()
            if i[:1] != "_" and i not in ["collection", "verbose_name", "id"]
        ]
        # self._collection_operations[collection] = operations

    def get_merge_comparison_hash(
        self, collection: Collection, model: PartialModel
    ) -> int | str:
        """Should be overridden by sub-classes to have helpful comparison values per collection"""
        return model["id"]  # should never merge models

    def handle_special_field(
        self,
        collection: Collection,
        field: CollectionField,
        into_: PartialModel,
        ranked_others: list[PartialModel],
    ) -> Any | None:
        """
        Should be overridden by sub-classes and return whatever should be entered
        as the new value of the field, or None
        """
        # raise ActionException(
        #     f"Function for {collection} field {field} not yet implemented"
        # )

    def execute_merge_on_reference_fields(
        self,
        field: CollectionField,
        into: PartialModel,
        ranked_others: list[PartialModel],
    ) -> list[int] | None:
        result = list(
            {id_ for model in [into, *ranked_others] for id_ in model.get(field, [])}
        )
        if len(result):
            return result
        return None

    def execute_deep_merge_on_reference_fields(
        self,
        field_collection: Collection,
        field: CollectionField,
        into: PartialModel,
        ranked_others: list[PartialModel],
        update_operations: dict[Collection, MergeUpdateOperations],
        with_create: bool = False,
    ) -> list[int] | None:
        if field_collection not in self._collection_field_groups:
            return self.execute_merge_on_reference_fields(field, into, ranked_others)
        all_field_ids: list[int] = [
            *into.get(field, []),
            *[id_ for model in ranked_others for id_ in model.get(field, [])],
        ]
        merge_lists: dict[Any, list[int]] = {}
        field_models = self.get_merge_by_rank_models(field_collection, all_field_ids)
        for id_ in all_field_ids:
            hash_val = self.get_merge_comparison_hash(
                field_collection, field_models[id_]
            )
            if hash_val in merge_lists:
                if id_ not in merge_lists[hash_val]:
                    merge_lists[hash_val].append(id_)
            else:
                merge_lists[hash_val] = [id_]
        new_reference_ids: list[int] = []
        # payloads: list[dict[str, Any]] = []
        for to_merge in merge_lists.values():
            if len(to_merge) > 1:
                as_create = with_create and to_merge[0] not in into.get(field, [])
                to_merge_into, to_merge_others = self.split_merge_by_rank_models(
                    to_merge[0],
                    to_merge[1:],
                    field_models,
                )
                if as_create:
                    to_merge_others = [to_merge_into, *to_merge_others]
                    to_merge_into = {}
                result = self.merge_by_rank(
                    field_collection,
                    to_merge_into,
                    to_merge_others,
                    {},
                    update_operations,
                )
                if as_create:
                    result.pop(field, [])
                    update_operations[field_collection]["create"].append(result)
                else:
                    result["id"] = to_merge[0]
                    update_operations[field_collection]["update"].append(result)
            elif with_create:
                if to_merge[0] not in into.get(field, []):
                    model, _ = self.split_merge_by_rank_models(
                        to_merge[0],
                        [],
                        field_models,
                    )
                    for rem_field in self._collection_field_groups[
                        field_collection
                    ].get("ignore", []):
                        model.pop(rem_field, None)
                    model.pop("id")
                    update_operations[field_collection]["create"].append(model)
                    update_operations[field_collection]["delete"].append(to_merge[0])
            if not with_create:
                new_reference_ids.append(to_merge[0])
        if len(new_reference_ids):
            return new_reference_ids
        return None

    def merge_by_rank(
        self,
        collection: Collection,
        into: PartialModel,
        ranked_others: list[PartialModel],
        instance: dict[str, Any],
        update_operations: dict[Collection, MergeUpdateOperations],
        should_create: bool = False,
    ) -> dict[str, Any]:
        merge_modes = self._collection_field_groups[collection]
        changes: dict[str, Any] = {}
        for field in merge_modes.get("error", []):
            for model in [into, *ranked_others]:
                if model.get(field) is not None:
                    raise ActionException(
                        f"Cannot merge {collection} models that have {field} set: Problem in {collection}/{model['id']}"
                    )
        for field in merge_modes.get("priority", []):
            for model in [into, *ranked_others]:
                if date := model.get(field):
                    changes[field] = date
                    break
        for field in merge_modes.get("highest", []):
            comp_data = [
                date
                for model in [into, *ranked_others]
                if (date := model.get(field)) is not None
            ]
            if len(comp_data):
                changes[field] = max(comp_data)
        for field in merge_modes.get("lowest", []):
            comp_data = [
                date
                for model in [into, *ranked_others]
                if (date := model.get(field)) is not None
            ]
            if len(comp_data):
                changes[field] = min(comp_data)
        for field in merge_modes.get("require_equality", []):
            eq_data = {
                date
                for model in [into, *ranked_others]
                if (date := model.get(field)) is not None
            }
            if (length := len(eq_data)) == 1:
                changes[field] = eq_data.pop()
            elif length > 1:
                raise ActionException(
                    f"Differing values in field {field} when merging into {collection}/{into['id']}"
                )
        for field in merge_modes.get("merge", []):
            if change := self.execute_merge_on_reference_fields(
                field, into, ranked_others
            ):
                changes[field] = sorted(change)
        for field in merge_modes.get("special_function", []):
            result = self.handle_special_field(collection, field, into, ranked_others)
            if result is not None:
                changes[field] = result
        for field, field_collection in merge_modes.get("deep_merge", {}).items():
            if change := self.execute_deep_merge_on_reference_fields(
                field_collection, field, into, ranked_others, update_operations
            ):
                changes[field] = change
        for field, field_collection in merge_modes.get("deep_create_merge", {}).items():
            self.execute_deep_merge_on_reference_fields(
                field_collection, field, into, ranked_others, update_operations, True
            )
        update_operations[collection]["delete"].extend(
            [
                model["id"]
                for model in (
                    [into, *ranked_others] if should_create else ranked_others
                )
            ]
        )
        changes.update(
            {key: value for key, value in instance.items() if key != "user_ids"}
        )
        # TODO: Check if data is valid
        return changes

    def get_merge_by_rank_models(
        self, collection: Collection, ids: list[int]
    ) -> dict[int, PartialModel]:
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    collection,
                    ids,
                    ["id", *self._all_collection_fields[collection]],
                )
            ]
        )[collection]
        for date in result.values():
            date.pop("meta_position", None)
        return result

    def split_merge_by_rank_models(
        self,
        into_id: int,
        ranked_other_ids: list[int],
        models: dict[int, PartialModel],
    ) -> tuple[PartialModel, list[PartialModel]]:
        return (
            models[into_id],
            [model for id_ in ranked_other_ids if (model := models.get(id_))],
        )