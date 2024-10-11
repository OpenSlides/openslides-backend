from collections import defaultdict
from typing import Any, TypedDict

from datastore.migrations.core.migration_reader import MigrationReader
from datastore.reader.core.requests import GetManyRequestPart
from datastore.shared.util import (
    collection_and_id_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from datastore.writer.core import (
    BaseRequestEvent,
    RequestDeleteEvent,
    RequestUpdateEvent,
)


class CollectionDeletionSchema(TypedDict):
    deletes_models_from: dict[str, list[str]]  # {collection: ids_fields}
    updates_models_from: dict[
        str, dict[str, str]
    ]  # {collection: {ids_field : foreign_ids_field}}


MigrationDeletionSchema = dict[str, CollectionDeletionSchema]


class DeletionMixin:
    """
    This class is used to delete cascading models genericly.
    It should only be used in migration context, where a MigrationReader is available.
    """

    reader: MigrationReader

    def delete_update_by_schema(
        self,
        initial_deletions: dict[str, set[int]],
        deletion_schema: MigrationDeletionSchema,
        events: list[BaseRequestEvent],
    ) -> None:
        """
        This recursively deletes all models specified by initial_deletions and the MigrationDeletionSchema.
        Also updates all relations in other models related to deleted models by the specifics of the MigrationDeletionSchema.
        This function auto magically handles 1:1, 1:n, n:m relations. It can also handle generic relations.
        If the update relations foreign field is of generic type the field name needs to be prefixed with "generic-".
        Can also delete models referenced within the same collection recursively.
        Returns the list of delete and update requests.
        """

        update_schema: defaultdict[str, list[str]] = defaultdict(list)
        for schema_part in deletion_schema.values():
            for collection, relation_fields in schema_part.get(
                "updates_models_from", {}
            ).items():
                for foreign_ids_field in relation_fields.values():
                    if "generic-" in foreign_ids_field:
                        foreign_ids_field = foreign_ids_field.lstrip("generic-")
                    update_schema[collection].append(foreign_ids_field)
        # dicts structure is {collection : id : fields : values}
        to_be_updated: dict[str, dict[int, dict[str, list[str | int]]]] = {
            collection: defaultdict(lambda: defaultdict(list[str | int]))
            for collection in update_schema.keys()
        }
        to_be_deleted: dict[str, set[int]] = {
            collection: set() for collection in deletion_schema.keys()
        }

        # set deletion root by finding statute related motions
        # for collection, to_delete_ids in initial_deletions.items():
        #     to_be_deleted[collection] = to_delete_ids
        # delete until all collections in to_be_deleted have at least an empty list (means finished)
        self._recursively_stage_for_deletion_and_rel_for_update(
            initial_deletions,
            deletion_schema,
            to_be_deleted,
            to_be_updated,
        )
        self.delete_all(to_be_deleted, events)
        # update lost references in bulk
        for collection, update_schema_part in update_schema.items():
            self.update_collection(
                events,
                collection,
                update_schema_part,
                to_be_updated[collection],
                to_be_deleted,
            )

    def _recursively_stage_for_deletion_and_rel_for_update(
        self,
        initial_deletes: dict[str, set[int]],
        delete_schema: MigrationDeletionSchema,
        to_be_deleted: dict[str, set[int]],
        to_be_updated: dict[str, dict[int, dict[str, list[int | str]]]],
    ) -> None:
        """
        Marks all models for deletion noted by the fields in collection_delete_schema.
        Marks all models for update noted by the fields in collection_delete_schema.
        """
        to_be_staged_recursively: defaultdict[str, set[int]] = defaultdict(set)
        for collection, model_ids in initial_deletes.items():
            to_be_deleted[collection].update(model_ids)
        for collection, collection_delete_schema in delete_schema.items():
            # get models to be deleted later
            if (to_be_deleted_ids := initial_deletes.get(collection)) and (
                fields := [
                    field_name
                    for field_names in collection_delete_schema.get(
                        "deletes_models_from", {}
                    ).values()
                    for field_name in field_names
                ]
                + [
                    field_name
                    for relation_fields in collection_delete_schema.get(
                        "updates_models_from", {}
                    ).values()
                    for field_name in relation_fields.keys()
                ]
            ):
                models = self.reader.get_many(
                    [GetManyRequestPart(collection, list(to_be_deleted_ids), fields)]
                ).get(collection, {})
                for model_id, model in models.items():
                    self._stage_for_update(
                        collection_delete_schema.get("updates_models_from", {}),
                        model,
                        model_id,
                        to_be_updated,
                        collection,
                    )
                    # stage related collection instances for later deletion
                    for foreign_collection, own_fields in collection_delete_schema.get(
                        "deletes_models_from", {}
                    ).items():
                        for own_field in own_fields:
                            # assert foreign_collection != collection
                            if foreign_id_or_ids := model.get(own_field):
                                if isinstance(foreign_id_or_ids, list) and isinstance(
                                    foreign_id_or_ids[0], str
                                ):
                                    foreign_id_or_ids = [
                                        id_from_fqid(foreign_id)
                                        for foreign_id in foreign_id_or_ids
                                    ]
                                elif isinstance(foreign_id_or_ids, str):
                                    foreign_id_or_ids = [
                                        id_from_fqid(foreign_id_or_ids)
                                    ]
                                elif isinstance(foreign_id_or_ids, int):
                                    foreign_id_or_ids = [foreign_id_or_ids]
                                for foreign_id in foreign_id_or_ids:
                                    if (
                                        foreign_id
                                        not in to_be_deleted[foreign_collection]
                                    ):
                                        to_be_staged_recursively[
                                            foreign_collection
                                        ].add(foreign_id)
        if any(to_be_staged_recursively):
            self._recursively_stage_for_deletion_and_rel_for_update(
                to_be_staged_recursively, delete_schema, to_be_deleted, to_be_updated
            )

    def _stage_for_update(
        self,
        collection_schema_updates_models_from: dict[str, dict[str, str]],
        model: dict[str, Any],
        model_id: int,
        to_be_updated: dict[str, dict[int, dict[str, list[int | str]]]],
        collection: str,
    ) -> None:
        """ stage instance ids for update in related collection instances """
        for (
            foreign_collection,
            relation_fields,
        ) in collection_schema_updates_models_from.items():
            for own_field, foreign_field in relation_fields.items():
                if "generic-" in foreign_field:
                    foreign_field = foreign_field.lstrip("generic-")
                    target_field_generic = True
                else:
                    target_field_generic = False
                if foreign_ids := model.get(own_field):
                    if not isinstance(foreign_ids, list):
                        foreign_ids = [foreign_ids]
                    for foreign_id in foreign_ids:
                        if isinstance(foreign_id, str):
                            tmp_foreign_collection, foreign_id = (
                                collection_and_id_from_fqid(foreign_id)
                            )
                            # generic fields can have different collections in fqid thus differing from target collection.
                            # will be treated by the next combination of this field and collection
                            if tmp_foreign_collection != foreign_collection:
                                continue
                        # need to store own collection context for generic foreign field
                        if target_field_generic:
                            model_id_or_fqid: str | int = fqid_from_collection_and_id(
                                collection, model_id
                            )
                        else:
                            model_id_or_fqid = model_id
                        to_be_updated[foreign_collection][foreign_id][
                            foreign_field
                        ].append(model_id_or_fqid)

    def delete_all(
        self, to_be_deleted: dict[str, set[int]], events: list[BaseRequestEvent]
    ) -> None:
        """ Creates RequestDeleteEvents for models given in to_be_deleted """
        for collection, to_be_deleted_ids in to_be_deleted.items():
            if to_be_deleted_ids:
                for to_be_deleted_id in to_be_deleted_ids:
                    events.append(
                        RequestDeleteEvent(
                            fqid_from_collection_and_id(collection, to_be_deleted_id)
                        )
                    )

    def update_collection(
        self,
        events: list,
        collection: str,
        collection_update_schema: list[str],
        to_be_updated_in_collection: dict[int, dict[str, Any]],
        deleted_instances: dict[str, set[int]],
    ) -> None:
        """
        Updates all models of the collection with the info provided by the collection_update_schema
        but not those that were already deleted.
        """
        to_remove = []
        # if there were no instances deleted we don't need to remove them from our update list.
        if collections_deleted_ids := deleted_instances.get(collection):
            for instance_id in to_be_updated_in_collection.keys():
                if instance_id in collections_deleted_ids:
                    to_remove.append(instance_id)
            for instance_id in to_remove:
                del to_be_updated_in_collection[instance_id]

        instances = self.reader.get_many(
            [
                GetManyRequestPart(
                    collection,
                    [instance_id for instance_id in to_be_updated_in_collection.keys()],
                    collection_update_schema,
                )
            ]
        ).get(collection, {})
        for instance_id, fields_and_ids in to_be_updated_in_collection.items():
            instance = instances.get(instance_id, {})
            # save the instances data without the deleted ids
            for field, without_ids in fields_and_ids.items():
                db_ids = instance.get(field, [])
                if not isinstance(db_ids, list):
                    db_ids = [instance.get(field, [])]
                fields_and_ids[field] = self.subtract_ids(db_ids, without_ids)
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id(collection, instance_id), fields_and_ids
                )
            )

    def subtract_ids(
        self, front_ids: list | None, without_ids: list | None
    ) -> list | None:
        """
        This subtracts items of a list from another list in an efficient manner.
        Returns a list.
        """
        if not front_ids:
            return None
        if not without_ids:
            return front_ids
        return list(set(front_ids) - set(without_ids)) or None
