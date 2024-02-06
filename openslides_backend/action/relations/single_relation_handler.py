from collections import defaultdict
from collections.abc import Iterable
from typing import Any, Union, cast

from datastore.shared.util import DeletedModelsBehaviour

from ...models.base import model_registry
from ...models.fields import (
    BaseGenericRelationField,
    BaseRelationField,
    GenericRelationField,
    GenericRelationListField,
    RelationField,
    RelationListField,
)
from ...services.datastore.interface import DatastoreService, PartialModel
from ...shared.exceptions import ActionException
from ...shared.patterns import (
    Collection,
    FullQualifiedId,
    collection_from_fqid,
    fqfield_from_fqid_and_field,
    fqid_from_collection_and_id,
    id_from_fqid,
    transform_to_fqids,
)
from .typing import FieldUpdateElement, RelationFieldUpdates


class SingleRelationHandler:
    """
    This class combines serveral methods to calculate changes of relation fields.

    There are the following distinctions:
        by type: 1:1, 1:m, m:1 or m:n
        by field: normal field
        by content: integer relation and generic relation (using a full qualified id)

    Therefor we have many cases this class has to handle.
    """

    def __init__(
        self,
        datastore: DatastoreService,
        field: BaseRelationField,
        field_name: str,
        instance: dict[str, Any],
    ) -> None:
        self.datastore = datastore
        self.model = model_registry[field.own_collection]
        self.id = instance["id"]
        self.field = field
        self.field_name = field_name
        self.instance = instance
        self.chained_fqids: list[FullQualifiedId] = []

    def get_reverse_field(self, collection: Collection) -> BaseRelationField:
        """
        Returns the reverse field of this relation field for the given collection.
        """
        related_name = self.field.to[collection]
        field = model_registry[collection]().get_field(related_name)
        assert isinstance(field, BaseRelationField)
        return field

    def get_field_type(self, collection: Collection | None = None) -> str:
        """
        Returns one of the following types: 1:1, 1:m, m:1 or m:n
        """
        if isinstance(self.field, GenericRelationField) and len(self.field.to) > 1:
            if value := self.instance.get(self.field_name):
                collection = collection_from_fqid(value)
                if collection not in self.field.to:
                    raise ActionException(
                        f"The collection '{collection}' is not available for field '{self.field.own_field_name}' in collection '{self.field.own_collection}'."
                    )
            elif not collection:
                raise ActionException(
                    f"Cannot determine field type for {self.field.own_collection}/{self.field.own_field_name}."
                )
        else:
            collection = self.field.get_target_collection()
        reverse_field = self.get_reverse_field(collection)
        if isinstance(self.field, RelationField) or isinstance(
            self.field, GenericRelationField
        ):
            if not reverse_field.is_list_field:
                return "1:1"
            return "1:m"
        else:
            assert isinstance(self.field, RelationListField) or isinstance(
                self.field, GenericRelationListField
            )
            if not reverse_field.is_list_field:
                return "m:1"
            return "m:n"

    def perform(self) -> RelationFieldUpdates:
        """
        Main method of this handler. It calculates which relation fields have to be updated
        according to the changes in self.field.
        """
        # Prepare the new value of our field and the real field name of the reverse field.
        value = self.instance.get(self.field_name)
        rel_ids = transform_to_fqids(value, self.field.get_target_collection())
        # We transform everything to lists of fqids to unify the handling. The values are
        # later transformed back

        # calculated the fqids which have to be added/remove and partition them by collection
        # since every collection might have a different related field
        add, remove = self.relation_diffs(rel_ids)
        changed_fqids = list(add | remove)

        add_per_collection = self.partition_by_collection(add)
        remove_per_collection = self.partition_by_collection(remove)
        changed_fqids_per_collection = self.partition_by_collection(changed_fqids)

        final = {}
        for collection in list(add_per_collection.keys()) + list(
            remove_per_collection.keys()
        ):
            if collection not in self.field.to:
                raise ActionException(
                    f"The collection '{collection}' is not available for field '{self.field.own_field_name}' in collection '{self.field.own_collection}'."
                )

            related_name = self.get_related_name(collection)
            related_field = self.get_reverse_field(collection)

            # acquire all related models with the related fields
            rels: dict[FullQualifiedId, PartialModel] = defaultdict(dict)
            for fqid in changed_fqids_per_collection[collection]:
                related_model = self.datastore.get(
                    fqid,
                    [related_name],
                    get_deleted_models=DeletedModelsBehaviour.NO_DELETED,
                    raise_exception=False,
                )
                # again, we transform everything to lists of fqids
                rels[fqid][related_name] = transform_to_fqids(
                    related_model.get(related_name), self.model.collection
                )

            # calculate actual updates
            result = self.prepare_result(
                add_per_collection[collection],
                remove_per_collection[collection],
                rels,
                related_name,
            )
            for rel_update in result.values():
                # transform fqids back to ids
                if not isinstance(related_field, BaseGenericRelationField):
                    modified_element = rel_update["modified_element"]
                    assert not isinstance(modified_element, int)
                    rel_update["modified_element"] = id_from_fqid(
                        cast(FullQualifiedId, modified_element)
                    )

                    fqids = cast(list[FullQualifiedId], rel_update["value"])
                    rel_update["value"] = [id_from_fqid(fqid) for fqid in fqids]

                # remove arrays in *:1 cases which we artificially added
                current_value = cast(
                    Union[list[int], list[FullQualifiedId]], rel_update["value"]
                )
                if self.get_field_type(collection) in ("1:1", "m:1"):
                    if len(current_value) == 0:
                        rel_update["value"] = None
                    else:
                        rel_update["value"] = current_value[0]

            final.update(result)

        for fqid in self.chained_fqids:
            handler = self.build_handler_from_chained_fqid(fqid)
            result = handler.perform()
            final.update(result)
        return final

    def build_handler_from_chained_fqid(
        self, fqid: FullQualifiedId
    ) -> "SingleRelationHandler":
        collection = collection_from_fqid(fqid)
        field_name = self.get_related_name(collection)
        field = self.get_reverse_field(collection)
        instance = self.datastore.get(fqid, ["id", field_name])
        instance[field_name] = None
        return SingleRelationHandler(
            self.datastore,
            field,
            field_name,
            instance,
        )

    def partition_by_collection(
        self, fqids: Iterable[FullQualifiedId]
    ) -> dict[Collection, list[FullQualifiedId]]:
        """
        Takes the given FQIDs and partitions them by their collection.
        """
        partition = defaultdict(list)
        for fqid in fqids:
            partition[collection_from_fqid(fqid)].append(fqid)
        return partition

    def get_related_name(self, collection: Collection) -> str:
        return self.field.to[collection]

    def relation_diffs(
        self, rel_fqids: list[FullQualifiedId]
    ) -> tuple[set[FullQualifiedId], set[FullQualifiedId]]:
        """
        Returns two sets of relation object ids. One with relation objects
        where object should be added and one with relation objects where it
        should be removed.
        """
        add: set[FullQualifiedId]
        remove: set[FullQualifiedId]
        # We have to compare with the current datastore state.
        # Retrieve current object from datastore
        current_obj = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, self.id),
            [self.field_name],
            use_changed_models=False,
            raise_exception=False,
        )

        # Get current ids from relation field
        current_value = current_obj.get(self.field_name)
        current_fqids = set(
            transform_to_fqids(current_value, self.field.get_target_collection())
        )

        # Calculate add set and remove set
        new_fqids = set(rel_fqids)
        add = new_fqids - current_fqids
        # filter out deleted models, so that in case of cascade deletion no data is lost
        remove = {
            fqid
            for fqid in current_fqids - new_fqids
            if not self.datastore.is_deleted(fqid)
        }

        return add, remove

    def prepare_result(
        self,
        add: list[FullQualifiedId],
        remove: list[FullQualifiedId],
        rels: dict[FullQualifiedId, PartialModel],
        related_name: str,
    ) -> RelationFieldUpdates:
        """
        Final method to prepare the result i. e. the new value of the relation field.
        """
        relations: RelationFieldUpdates = {}
        for fqid, rel in rels.items():
            new_value: Any  # Union[FullQualifiedId, List[FullQualifiedId]]
            own_fqid = fqid_from_collection_and_id(self.field.own_collection, self.id)
            if fqid in add:
                if own_fqid in rel[related_name]:
                    continue
                if rel[related_name] and self.get_field_type() in ("1:1", "m:1"):
                    assert len(rel[related_name]) == 1
                    self.chained_fqids.append(fqid)
                    new_value = [own_fqid]
                else:
                    new_value = rel[related_name] + [own_fqid]
                rel_element = FieldUpdateElement(
                    type="add", value=new_value, modified_element=own_fqid
                )
            else:
                assert fqid in remove
                new_value = rel[related_name]
                if own_fqid not in new_value:
                    continue  # maybe replaced by other action
                new_value.remove(own_fqid)
                rel_element = FieldUpdateElement(
                    type="remove", value=new_value, modified_element=own_fqid
                )
            fqfield = fqfield_from_fqid_and_field(fqid, related_name)
            relations[fqfield] = rel_element
        return relations
