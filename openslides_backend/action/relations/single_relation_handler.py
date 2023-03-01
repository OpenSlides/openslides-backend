from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union, cast

from datastore.shared.util import DeletedModelsBehaviour

from ...models.base import model_registry
from ...models.fields import (
    BaseGenericRelationField,
    BaseRelationField,
    BaseTemplateField,
    BaseTemplateRelationField,
    GenericRelationField,
    GenericRelationListField,
    RelationField,
    RelationListField,
)
from ...services.datastore.interface import (
    DatastoreService,
    GetManyRequest,
    PartialModel,
)
from ...shared.exceptions import ActionException
from ...shared.patterns import (
    Collection,
    FullQualifiedId,
    collection_from_fqfield,
    collection_from_fqid,
    fqfield_from_fqid_and_field,
    fqid_from_collection_and_id,
    fqid_from_fqfield,
    id_from_fqfield,
    id_from_fqid,
    transform_to_fqids,
)
from .typing import FieldUpdateElement, RelationFieldUpdates


class SingleRelationHandler:
    """
    This class combines serveral methods to calculate changes of relation fields.

    There are the following distinctions:
        by type: 1:1, 1:m, m:1 or m:n
        by field: normal field or with structured field or template field
        by content: integer relation and generic relation (using a full qualified id)

    Therefor we have many cases this class has to handle.
    """

    def __init__(
        self,
        datastore: DatastoreService,
        field: BaseRelationField,
        field_name: str,
        instance: Dict[str, Any],
    ) -> None:
        self.datastore = datastore
        self.model = model_registry[field.own_collection]
        self.id = instance["id"]
        self.field = field
        self.field_name = field_name
        self.instance = instance
        self.chained_fields: List[Dict[str, Any]] = []

    def get_reverse_field(self, collection: Collection) -> BaseRelationField:
        """
        Returns the reverse field of this relation field for the given collection.
        """
        related_name = self.field.to[collection]
        field = model_registry[collection]().get_field(related_name)
        assert isinstance(field, BaseRelationField)
        return field

    def get_field_type(self, collection: Optional[Collection] = None) -> str:
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

        # Just check if we have an invalid use case here.
        if isinstance(self.field, BaseTemplateRelationField):
            if self.field.is_template_field(self.field_name):
                raise ValueError(
                    "You can not handle template fields here. Use them with populated replacements."
                )

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
            rels: Dict[FullQualifiedId, PartialModel] = defaultdict(dict)
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
            for fqfield, rel_update in result.items():
                # transform fqids back to ids
                if not isinstance(related_field, BaseGenericRelationField):
                    modified_element = rel_update["modified_element"]
                    assert type(modified_element) != int
                    rel_update["modified_element"] = id_from_fqid(
                        cast(FullQualifiedId, modified_element)
                    )

                    fqids = cast(List[FullQualifiedId], rel_update["value"])
                    rel_update["value"] = [id_from_fqid(fqid) for fqid in fqids]

                # remove arrays in *:1 cases which we artificially added
                current_value = cast(
                    Union[List[int], List[FullQualifiedId]], rel_update["value"]
                )
                if self.get_field_type(collection) in ("1:1", "m:1"):
                    if len(current_value) == 0:
                        rel_update["value"] = None
                    else:
                        rel_update["value"] = current_value[0]

            final.update(result)

            # update the reverse template field in the case of a structured field
            if isinstance(related_field, BaseTemplateField):
                result_template_field = self.prepare_result_template_field(result)
                final.update(result_template_field)

        for chained_field in self.chained_fields:
            handler = self.build_handler_from_chained_field(chained_field)
            result = handler.perform()
            final.update(result)
        return final

    def build_handler_from_chained_field(self, chained_field: Dict[str, Any]):  # type: ignore
        """
        "field": self.field.to,
        "fqid": fqid,
        "origin_modified_fqid": own_fqid,
        """
        collection = collection_from_fqid(chained_field["fqid"])
        field_name = self.get_related_name(collection)
        field = self.get_reverse_field(collection)
        instance = self.datastore.get(chained_field["fqid"], ["id", field_name])
        instance[field_name] = None
        return SingleRelationHandler(
            self.datastore,
            field,
            field_name,
            instance,
        )

    def partition_by_collection(
        self, fqids: Iterable[FullQualifiedId]
    ) -> Dict[Collection, List[FullQualifiedId]]:
        """
        Takes the given FQIDs and partitions them by their collection.
        """
        partition = defaultdict(list)
        for fqid in fqids:
            partition[collection_from_fqid(fqid)].append(fqid)
        return partition

    def get_related_name(self, collection: Collection) -> str:
        """
        Get the field name of the reverse field. In case of a structured field it is
        populated with the replacement (either some id e. g. of a meeting or some tag).
        """
        field_name = self.field.to[collection]
        related_field = self.get_reverse_field(collection)
        if not isinstance(related_field, BaseTemplateField):
            return field_name
        else:
            if not isinstance(self.field, BaseTemplateField):
                # We have a one-sided structured relation, insert replacement
                assert related_field.replacement_collection
                replacement_field = str(related_field.replacement_collection) + "_id"
                replacement = self.instance.get(replacement_field)
                if replacement is None:
                    # replacement field was not fetched from db yet
                    db_instance = self.datastore.get(
                        fqid=fqid_from_collection_and_id(
                            self.model.collection, self.id
                        ),
                        mapped_fields=[replacement_field],
                        use_changed_models=False,
                    )
                    replacement = db_instance.get(replacement_field)
                    assert replacement
            else:
                # We have a structured tag. Extract the replacement directly from
                # the field name
                replacement = self.field.get_replacement(self.field_name)
            return related_field.get_structured_field_name(replacement)

    def relation_diffs(
        self, rel_fqids: List[FullQualifiedId]
    ) -> Tuple[Set[FullQualifiedId], Set[FullQualifiedId]]:
        """
        Returns two sets of relation object ids. One with relation objects
        where object should be added and one with relation objects where it
        should be removed.
        """
        add: Set[FullQualifiedId]
        remove: Set[FullQualifiedId]
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
        add: List[FullQualifiedId],
        remove: List[FullQualifiedId],
        rels: Dict[FullQualifiedId, PartialModel],
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
                    self.chained_fields.append(
                        {
                            "field": self.field.to,
                            "fqid": fqid,
                        }
                    )
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

    def prepare_result_template_field(
        self, result_structured_field: RelationFieldUpdates
    ) -> RelationFieldUpdates:
        """
        We also have to update the raw template field.
        """
        if not result_structured_field:
            return {}

        collection = collection_from_fqfield(next(iter(result_structured_field)))
        related_name = self.get_related_name(collection)
        reverse_field = self.get_reverse_field(collection)
        assert isinstance(reverse_field, BaseTemplateField)
        template_field_name = self.field.to[collection]

        # assert that the related name contains a valid replacement
        replacement = reverse_field.get_replacement(related_name)

        ids = [id_from_fqfield(fqfield) for fqfield in result_structured_field.keys()]
        response = self.datastore.get_many(
            get_many_requests=[
                GetManyRequest(collection, ids, mapped_fields=[template_field_name])
            ],
        )
        db_rels = response.get(collection, {})
        result_template_field: RelationFieldUpdates = {}
        for fqfield, rel_update in result_structured_field.items():
            current_value = db_rels.get(id_from_fqfield(fqfield), {}).get(
                template_field_name, []
            )
            field_type = self.get_field_type(collection)
            if (field_type in ("1:1", "m:1") and rel_update["value"] is None) or (
                field_type in ("1:m", "m:n") and rel_update["value"] == []
            ):
                # The field was emptied, so we have to remove the replacement.
                current_value.remove(replacement)
                rel_element = FieldUpdateElement(
                    type="remove", value=current_value, modified_element=replacement
                )
            elif rel_update["type"] == "add" and (
                field_type in ("1:1", "m:1")
                or (
                    field_type in ("1:m", "m:n")
                    and isinstance(rel_update["value"], list)
                    and len(rel_update["value"]) == 1
                )
            ):
                # The replacement was added just now, so we have to add it to the template field.
                if replacement in current_value:
                    continue
                rel_element = FieldUpdateElement(
                    type="add",
                    value=current_value + [replacement],
                    modified_element=replacement,
                )
            else:
                # Nothing to do, replacement already existed and still exists. Skip.
                continue
            result_template_field[
                fqfield_from_fqid_and_field(
                    fqid_from_fqfield(fqfield),
                    template_field_name,
                )
            ] = rel_element
        return result_template_field
