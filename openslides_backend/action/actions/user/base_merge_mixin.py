from typing import Any, TypedDict, cast

from openslides_backend.services.datastore.interface import PartialModel

from ....models.base import Model
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.interfaces.event import EventType
from ....shared.patterns import (
    Collection,
    CollectionField,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from ...action import Action, ActionResults, WriteRequest
from ...util.typing import ActionData


class MergeModeDict(TypedDict, total=False):
    ignore: list[CollectionField]
    # raise exception if set on any user
    error: list[CollectionField]
    # error if all examples of the field that are set aren't the same,
    # otherwise use that value
    require_equality: list[CollectionField]
    require_equality_absolute: list[CollectionField]
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
        self._collection_back_fields: dict[Collection, str] = {}
        self._collection_parents: dict[Collection, Collection] = {}

    def mass_prefetch_for_merge(
        self, collection_to_ids: dict[Collection, list[int]]
    ) -> None:
        data = self.datastore.get_many(
            [
                GetManyRequest(
                    collection,
                    ids,
                    self._all_collection_fields[collection],
                )
                for collection, ids in collection_to_ids.items()
            ]
        )
        mass_prefetch_payload: dict[Collection, list[int]] = {}
        for collection, collection_data in data.items():
            field_groups = self._collection_field_groups.get(collection, {})
            recurse = {
                **field_groups.get("deep_merge", {}),
                **field_groups.get("deep_create_merge", {}),
            }
            for field, recurse_collection in recurse.items():
                ids: list[int] = []
                for date in collection_data.values():
                    ids.extend(date.get(field, []))
                if len(ids):
                    mass_prefetch_payload[recurse_collection] = ids
        if len(mass_prefetch_payload):
            self.mass_prefetch_for_merge(mass_prefetch_payload)

    def add_collection_field_groups(
        self,
        Class: type[Model],
        field_groups: MergeModeDict,
        back_field: str = "",
    ) -> None:
        """Should be called once in __init__ of every sub-class"""
        collection = Class.collection
        self._collection_field_groups[collection] = field_groups
        self._all_collection_fields[collection] = [
            i
            for i in Class.__dict__.keys()
            if i[:1] != "_" and i not in ["collection", "verbose_name", "id"]
        ]
        if back_field:
            self._collection_back_fields[collection] = back_field
        for child_collection in {
            **field_groups.get("deep_merge", {}),
            **field_groups.get("deep_create_merge", {}),
        }.values():
            self._collection_parents[child_collection] = collection

    def get_merge_comparison_hash(
        self, collection: Collection, model: PartialModel
    ) -> int | str | tuple[int | str, ...]:
        """Should be overridden by sub-classes to have helpful comparison values per collection"""
        return model["id"]  # should never merge models

    def handle_special_field(
        self,
        collection: Collection,
        field: CollectionField,
        into_: PartialModel,
        ranked_others: list[PartialModel],
        update_operations: dict[Collection, MergeUpdateOperations],
    ) -> Any | None:
        """
        Should be overridden by sub-classes and return whatever should be entered
        as the new value of the field, or None
        """
        raise ActionException(
            f"Function for {collection} field {field} not yet implemented"
        )

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
        merge_lists = {li[0]: li for li in merge_lists.values()}
        new_reference_ids: list[int] = []
        for to_merge in merge_lists.values():
            to_merge_into, to_merge_others = self.split_merge_by_rank_models(
                to_merge[0],
                to_merge[1:],
                field_models,
            )
            is_transfer = to_merge[0] not in into.get(field, [])
            if len(to_merge) > 1:
                as_create = with_create and is_transfer
                if as_create:
                    to_merge_others = [to_merge_into, *to_merge_others]
                result = self.merge_by_rank(
                    field_collection,
                    None if as_create else to_merge_into,
                    to_merge_others,
                    {},
                    update_operations,
                )
                if as_create:
                    result.pop(field, [])
                    for ignore_field in self._collection_field_groups[
                        field_collection
                    ].get("ignore", []):
                        if (
                            val := to_merge_into.get(ignore_field)
                        ) is not None and ignore_field != (
                            self._collection_back_fields.get(field_collection)
                        ):
                            result[ignore_field] = val
                    update_operations[field_collection]["create"].append(result)
                else:
                    result["id"] = to_merge[0]
                    update_operations[field_collection]["update"].append(result)
                self._history_replacement_groups[field_collection].append(
                    ({**to_merge_into, **result}, to_merge, is_transfer)
                )
            elif is_transfer:
                if with_create:
                    self.copy_create_model(
                        update_operations, field_collection, to_merge_into
                    )
                self._history_replacement_groups[field_collection].append(
                    (to_merge_into, to_merge, is_transfer)
                )
            if not with_create:
                new_reference_ids.append(to_merge[0])
        if len(new_reference_ids):
            return new_reference_ids
        return None

    def copy_create_model(
        self,
        update_operations: dict[Collection, MergeUpdateOperations],
        collection: Collection,
        merge_model: PartialModel,
    ) -> None:
        id_: int = merge_model.pop("id")
        if back := self._collection_back_fields.get(collection):
            merge_model.pop(back, 0)
        for field, sub_collection in (
            self._collection_field_groups[collection]
            .get("deep_create_merge", {})
            .items()
        ):
            ids: list[int] = merge_model.pop(field, [])
            if len(ids):
                field_models = self.get_merge_by_rank_models(sub_collection, ids)
                for model in field_models.values():
                    self.copy_create_model(update_operations, sub_collection, model)
        update_operations[collection]["create"].append(merge_model)
        update_operations[collection]["delete"].append(id_)

    def check_equality(
        self,
        collection: Collection,
        into: PartialModel | None,
        ranked_others: list[PartialModel],
        main_id: int,
        field: str,
        absolute: bool = False,
    ) -> Any | None:
        eq_data = {
            date
            for model in [into, *ranked_others]
            if model is not None
            and (((date := model.get(field)) is not None) or absolute)
        }
        if (length := len(eq_data)) == 1:
            return eq_data.pop()
        elif length > 1:
            raise ActionException(
                f"Differing values in field {field} when merging into {collection}/{main_id}"
            )
        return None

    def merge_by_rank(
        self,
        collection: Collection,
        into: PartialModel | None,
        ranked_others: list[PartialModel],
        instance: dict[str, Any],
        update_operations: dict[Collection, MergeUpdateOperations],
        should_create: bool = False,
    ) -> dict[str, Any]:
        """
        Main function for the merging of specific models using the collection_field_groups of this collection.

        Takes a main model `into`, into which the others will be merged,
        and a list of models `ranked_models`, that will be merged into the main model in-order.
        It returns the new data for the main model, which the calling function has to decide how to handle
        and also recursively handles the related collections and writes the changes of their models into the correct category
        of the update_operations dict that is passed to it.
        """
        into_dict = into or {}
        main_id = into_dict.get("id") or ranked_others[0]["id"]
        merge_modes = self._collection_field_groups[collection]
        changes: dict[str, Any] = {}
        for field in merge_modes.get("error", []):
            if model := next(
                (model for model in [into_dict, *ranked_others] if model.get(field)),
                None,
            ):
                raise ActionException(
                    f"Cannot merge {collection} models that have {field} set: Problem in {collection}/{model['id']}"
                )
        for field in merge_modes.get("require_equality", []):
            if result := self.check_equality(
                collection, into, ranked_others, main_id, field
            ):
                changes[field] = result
        for field in merge_modes.get("require_equality_absolute", []):
            if result := self.check_equality(
                collection, into, ranked_others, main_id, field, True
            ):
                changes[field] = result
        for field in merge_modes.get("special_function", []):
            result = self.handle_special_field(
                collection, field, into_dict, ranked_others, update_operations
            )
            if result is not None:
                changes[field] = result
        for field, field_collection in merge_modes.get("deep_merge", {}).items():
            if change := self.execute_deep_merge_on_reference_fields(
                field_collection, field, into_dict, ranked_others, update_operations
            ):
                changes[field] = change
        for field, field_collection in merge_modes.get("deep_create_merge", {}).items():
            self.execute_deep_merge_on_reference_fields(
                field_collection,
                field,
                into_dict,
                ranked_others,
                update_operations,
                True,
            )
        for field in merge_modes.get("merge", []):
            if change := self.execute_merge_on_reference_fields(
                field, into_dict, ranked_others
            ):
                changes[field] = sorted(change)
        for field in merge_modes.get("priority", []):
            if date := next(
                (
                    date
                    for model in [into_dict, *ranked_others]
                    if (date := model.get(field))
                ),
                None,
            ):
                changes[field] = date
        for category, func in [("highest", max), ("lowest", min)]:
            for field in cast(list[str], merge_modes.get(category, [])):
                if len(
                    comp_data := [
                        date
                        for model in [into_dict, *ranked_others]
                        if (date := model.get(field)) is not None
                    ]
                ):
                    changes[field] = func(comp_data)
        update_operations[collection]["delete"].extend(
            [
                model["id"]
                for model in (
                    [into_dict, *ranked_others] if should_create else ranked_others
                )
            ]
        )
        changes.update(
            {key: value for key, value in instance.items() if key != "user_ids"}
        )
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

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> tuple[WriteRequest | None, ActionResults | None]:
        self._history_replacement_groups: dict[
            Collection,
            list[tuple[dict[str, Any], list[int], bool]],
        ] = {}
        for collection in self._collection_field_groups:
            self._history_replacement_groups[collection] = []
        return super().perform(action_data, user_id, internal)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        self.main_fqid = fqid_from_collection_and_id(
            self.model.collection, instance["id"]
        )
        return super().update_instance(instance)

    def execute_other_action(
        self,
        ActionClass: type["Action"],
        action_data: ActionData,
        skip_archived_meeting_check: bool = True,
        skip_history: bool = True,
    ) -> ActionResults | None:
        return super().execute_other_action(
            ActionClass, action_data, skip_archived_meeting_check, skip_history
        )

    def build_write_request(self) -> WriteRequest | None:
        request = super().build_write_request()
        if request:
            fqids_in_events = {event["fqid"] for event in request.events}
            for fqid in request.information or {}:
                if fqid not in fqids_in_events:
                    request.events.append(
                        {
                            "type": EventType.Update,
                            "fqid": fqid,
                            "fields": {"id": id_from_fqid(fqid)},
                        }
                    )
        return request
