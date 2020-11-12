import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from mypy_extensions import TypedDict

from ...models.base import model_registry
from ...models.fields import (
    BaseRelationField,
    BaseTemplateField,
    BaseTemplateRelationField,
    GenericRelationField,
    GenericRelationListField,
    RelationField,
    RelationListField,
    TemplateRelationField,
    TemplateRelationListField,
)
from ...services.datastore.interface import (
    DatastoreService,
    GetManyRequest,
    PartialModel,
)
from ...shared.exceptions import ActionException, DatastoreException
from ...shared.patterns import (
    KEYSEPARATOR,
    Collection,
    FullQualifiedField,
    FullQualifiedId,
    to_fqid,
)
from ...shared.typing import DeletedModel, ModelMap

RelationsElement = TypedDict(
    "RelationsElement",
    {
        "type": str,
        "value": Optional[
            Union[int, FullQualifiedId, List[int], List[FullQualifiedId], List[str]]
        ],
        "modified_element": Union[int, FullQualifiedId, str],
    },
)
Relations = Dict[FullQualifiedField, RelationsElement]


class SingleRelationHandler:
    """
    This class combines serveral methods to calculate changes of relation fields.

    There are the following distinctions:
        by type: 1:1, 1:m, m:1 or m:n
        by field: normal field or with structured field or template field
        by content: integer relation and generic relation (using a full qualified id)

    Therefor we have many cases this class has to handle.

    additional_relation_models can provide models that are required for resolving the
    relations, but are not yet present in the datastore. This is necessary when nesting
    actions that are dependent on each other (e. g. topic.create calls
    agenda_item.create, which assumes the topic exists already).
    """

    def __init__(
        self,
        datastore: DatastoreService,
        field: BaseRelationField,
        field_name: str,
        instance: Dict[str, Any],
        only_add: bool = False,
        only_remove: bool = False,
        additional_relation_models: ModelMap = {},
    ) -> None:
        self.datastore = datastore
        self.model = model_registry[field.own_collection]
        self.id = instance["id"]
        self.field = field
        self.field_name = field_name
        self.instance = instance
        if only_add and only_remove:
            raise ValueError(
                "Do not set only_add and only_remove because this is contradictory."
            )
        self.only_add = only_add
        self.only_remove = only_remove
        self.additional_relation_models = additional_relation_models

        # Get reverse_field and field type
        self.reverse_field = self.get_reverse_field()
        self.type = self.get_field_type()

    def get_reverse_field(self) -> BaseRelationField:
        """
        Returns the reverse field of this relation field. In case of reverse generic relation
        we just take the first existing reverse field.
        """
        reverse_collection = self.field.to
        if isinstance(reverse_collection, list):
            reverse_collection = reverse_collection[0]
        if (
            self.field.structured_relation is not None
            or self.field.structured_tag is not None
        ):
            related_name = self.field.related_name.replace("$", "", 1)
        else:
            related_name = self.field.related_name
        field = model_registry[reverse_collection]().get_field(related_name)
        assert isinstance(field, BaseRelationField)
        return field

    def get_field_type(self) -> str:
        """
        Returns one of the following types: 1:1, 1:m, m:1 or m:n
        """
        if isinstance(self.field, RelationField) or isinstance(
            self.field, GenericRelationField
        ):
            if not self.reverse_field.is_list_field:
                return "1:1"
            return "1:m"
        else:
            assert isinstance(self.field, RelationListField) or isinstance(
                self.field, GenericRelationListField
            )
            if not self.reverse_field.is_list_field:
                return "m:1"
            return "m:n"

    def perform(self) -> Relations:
        """
        Main method of this handler. It calculates which relation fields have to be updated
        according to the changes in self.field.
        """
        # Prepare the new value of our field and the real field name of the reverse field.
        rel_ids = self.prepare_new_relation_ids()
        related_name = self.get_related_name()

        # Just check if we have an invalid use case here.
        if isinstance(self.field, TemplateRelationField) or isinstance(
            self.field, TemplateRelationListField
        ):
            if self.field_name.find("$_") > -1 or self.field_name[-1] == "$":
                raise ValueError(
                    "You can not handle raw template fields here. Use them with "
                    "populated replacements."
                )

        add: Union[Set[int], Set[FullQualifiedId]]
        remove: Union[Set[int], Set[FullQualifiedId]]
        rels: Union[Dict[int, PartialModel], Dict[FullQualifiedId, PartialModel]]
        ids: List[int]

        # Now perform everything:
        if isinstance(self.field, GenericRelationField) or isinstance(
            self.field, GenericRelationListField
        ):
            # Perform generic relation case.
            assert isinstance(self.field.to, list)
            rel_ids = cast(List[FullQualifiedId], rel_ids)
            add, remove = self.relation_diffs_fqid(rel_ids)
            fq_rels = {}
            for related_model_fqid in list(add | remove):
                if related_model_fqid.collection not in self.field.to:
                    raise RuntimeError(
                        "You try to change a generic relation field using foreign collections that are not available."
                    )
                related_model = self.fetch_model(
                    related_model_fqid,
                    [related_name],
                )
                fq_rels[related_model_fqid] = related_model
            rels = fq_rels
        else:
            # Perform non generic relation case.
            assert isinstance(self.field.to, Collection)
            rel_ids = cast(List[int], rel_ids)
            add, remove = self.relation_diffs(rel_ids)
            ids = list(add | remove)
            response = self.datastore.get_many(
                get_many_requests=[
                    GetManyRequest(self.field.to, ids, mapped_fields=[related_name])
                ],
                lock_result=True,
            )
            id_rels = response.get(self.field.to, {})

            # Switch type of values that represent a FQID
            # only in non-reverse generic relation case.
            if self.field.generic_relation:
                for rel_item in id_rels.values():
                    related_field_value = rel_item.get(related_name)
                    if related_field_value is not None:
                        if self.type in ("1:1", "m:1"):
                            rel_item[related_name] = to_fqid(related_field_value)
                        else:
                            assert self.type in ("1:m", "m:n")
                            new_related_field_value = []
                            for value_item in related_field_value:
                                new_related_field_value.append(to_fqid(value_item))
                            rel_item[related_name] = new_related_field_value

            # Inject additional_relation_models and check existance of target objects.
            for instance_id in ids:
                fqid = FullQualifiedId(self.field.to, instance_id)
                if fqid in self.additional_relation_models:
                    id_rels[instance_id] = self.additional_relation_models[fqid]
                if instance_id not in id_rels.keys():
                    raise ActionException(
                        f"You try to reference an instance of {self.field.to} that does not exist."
                    )
            rels = id_rels

        # Finally prepare result. We have three cases:
        #  - Reverse field is a generic relation field.
        #  - Reverse field is a template field.
        #  - All other fields.
        if self.field.generic_relation:
            return self.prepare_result_to_fqid(add, remove, rels, related_name)

        result = self.prepare_result_to_id(add, remove, rels, related_name)
        if not self.field.structured_relation and not self.field.structured_tag:
            return result
        else:
            assert ids is not None
            result_template_field = self.prepare_result_template_field(
                result, related_name, ids
            )
            return {**result, **result_template_field}

    def prepare_new_relation_ids(self) -> Union[List[int], List[FullQualifiedId]]:
        """
        Get the new value of our field as list. The list may be empty.
        """
        value = self.instance.get(self.field_name)
        if value is None:
            rel_ids = []
        else:
            # If if is 1:1 or 1:m we simulate a list of new values so we can
            # reuse the code here. In m:1 and m:n cases we can just take the
            # value.
            if self.type in ("1:1", "1:m"):
                rel_ids = [value]
            else:
                assert self.type in ("m:1", "m:n")
                rel_ids = value
        return rel_ids

    def get_related_name(self) -> str:
        """
        Get the field name of the reverse field. In case of a structured field it is
        populated with the replacement (either some id e. g. of a meeting or some tag).
        """
        if self.field.structured_relation is None and self.field.structured_tag is None:
            return self.field.related_name
        if self.field.structured_relation:
            replacement = self.search_structured_relation(
                list(self.field.structured_relation), self.model.collection, self.id
            )
            return self.field.related_name.replace("$", "$" + replacement)
        assert (
            self.field.structured_tag
            and isinstance(self.field, BaseTemplateRelationField)
            and isinstance(self.reverse_field, BaseTemplateRelationField)
        )
        replacement = self.field.get_replacement(self.field_name)
        return (
            self.field.related_name[: self.reverse_field.index]
            + "$"
            + replacement
            + self.field.related_name[self.reverse_field.index + 1 :]
        )

    def search_structured_relation(
        self,
        structured_relation: List[str],
        collection: Collection,
        id: int,
    ) -> str:
        """
        Recursive helper method to walk down the structured_relation field name list.
        """
        field_name = structured_relation.pop(0)
        # Try to find the field in self.obj. If this does not work, fetch it from DB.
        value = self.instance.get(field_name)
        if value is None:
            db_instance = self.datastore.get(
                fqid=FullQualifiedId(collection, id),
                mapped_fields=[field_name],
            )
            value = db_instance.get(field_name)
        if value is None:
            raise ValueError(
                f"The field {field_name} for {collection} must not be empty in datastore."
            )
        if structured_relation:
            new_field = model_registry[collection]().get_field(field_name)
            assert isinstance(new_field, BaseRelationField)
            new_collection = new_field.to
            assert isinstance(new_collection, Collection)
            return self.search_structured_relation(
                structured_relation, new_collection, value
            )
        return str(value)

    def fetch_model(
        self, fqid: FullQualifiedId, mapped_fields: List[str]
    ) -> Dict[str, Any]:
        if fqid in self.additional_relation_models and not isinstance(
            self.additional_relation_models[fqid], DeletedModel
        ):
            return {
                field: self.additional_relation_models[fqid].get(field)
                for field in mapped_fields
                if field in self.additional_relation_models[fqid]
            }
        else:
            try:
                return self.datastore.get(
                    fqid,
                    mapped_fields=mapped_fields,
                    lock_result=True,
                )
            except DatastoreException:
                return {}

    def relation_diffs(self, rel_ids: List[int]) -> Tuple[Set[int], Set[int]]:
        """
        Returns two sets of relation object ids. One with relation objects
        where object should be added and one with relation objects where it
        should be removed.

        This method is for relation case with integer ids.
        """
        add: Set[int]
        remove: Set[int]
        if self.only_add:
            # Add is equal to the relation ids. Remove is empty.
            add = set(rel_ids)
            remove = set()
        elif self.only_remove:
            raise NotImplementedError
        else:
            # We have to compare with the current datastore state.

            # Retrieve current object
            current_obj = self.fetch_model(
                FullQualifiedId(self.model.collection, self.id),
                [self.field_name],
            )

            # Get current ids from relation field
            if self.type in ("1:1", "1:m"):
                current_id = current_obj.get(self.field_name)
                if current_id is None:
                    current_ids = set()
                else:
                    current_ids = set([current_id])
            else:
                assert self.type in ("m:1", "m:n")
                current_ids = set(current_obj.get(self.field_name, []))

            # Calculate and return add set and remove set
            new_ids = set(rel_ids)
            add = new_ids - current_ids
            remove = current_ids - new_ids

        return add, remove

    def relation_diffs_fqid(
        self, rel_ids: List[FullQualifiedId]
    ) -> Tuple[Set[FullQualifiedId], Set[FullQualifiedId]]:
        """
        Returns two sets of relation object ids. One with relation objects
        where object should be added and one with relation objects where it
        should be removed.

        This method is for relation case with generic id using full qualified
        ids.
        """
        add: Set[FullQualifiedId]
        remove: Set[FullQualifiedId]
        if self.only_add:
            # Add is equal to the relation ids. Remove is empty.
            add = set(rel_ids)
            remove = set()
        elif self.only_remove:
            raise NotImplementedError
        else:
            # We have to compare with the current datastore state.

            # Retrieve current object from datastore
            current_obj = self.fetch_model(
                FullQualifiedId(self.model.collection, self.id),
                [self.field_name],
            )

            # Get current ids from relation field
            if self.type in ("1:1", "1:m"):
                current_id = current_obj.get(self.field_name)
                if current_id is None:
                    current_ids = set()
                else:
                    current_ids = set([current_id])
            else:
                assert self.type in ("m:1", "m:n")
                current_ids = set(current_obj.get(self.field_name, []))

            # Transform str to FullQualifiedId
            transformed_current_ids = set()
            for current_id in current_ids:
                transformed_current_ids.add(to_fqid(current_id))

            # Calculate add set and remove set
            new_ids = set(rel_ids)
            add = new_ids - transformed_current_ids
            remove = transformed_current_ids - new_ids

        return add, remove

    def prepare_result_to_id(
        self,
        add: Union[Set[int], Set[FullQualifiedId]],
        remove: Union[Set[int], Set[FullQualifiedId]],
        rels: Union[Dict[int, PartialModel], Dict[FullQualifiedId, PartialModel]],
        related_name: str,
    ) -> Relations:
        """
        Final method to prepare the result i. e. the new value of the relation field.

        Here the new value contains one or more ids.
        """
        relations: Relations = {}
        for rel_id, rel in sorted(rels.items(), key=lambda item: str(item[0])):
            new_value: Optional[Union[int, List[int]]]
            if rel_id in add:
                if self.type in ("1:1", "m:1"):
                    if rel.get(related_name) is None:
                        new_value = self.id
                    else:
                        if isinstance(rel_id, int):
                            msg = KEYSEPARATOR.join(
                                (str(self.field.to), str(rel_id), related_name)
                            )
                        else:
                            msg = KEYSEPARATOR.join((str(rel_id), related_name))
                        message = (
                            f"You can not set {msg} in to a new value because this "
                            "field is not empty."
                        )
                        raise ActionException(message)
                else:
                    assert self.type in ("1:m", "m:n")
                    new_value = rel.get(related_name, []) + [self.id]
                rel_element = RelationsElement(
                    type="add", value=new_value, modified_element=self.id
                )
            else:
                assert rel_id in remove
                if self.type in ("1:1", "m:1"):
                    new_value = None
                else:
                    assert self.type in ("1:m", "m:n")
                    if isinstance(rel, DeletedModel):
                        new_value = []
                    else:
                        new_value = rel[related_name]
                        assert isinstance(new_value, list)
                        new_value.remove(self.id)
                rel_element = RelationsElement(
                    type="remove", value=new_value, modified_element=self.id
                )
            if isinstance(rel_id, int):
                assert isinstance(self.field.to, Collection)
                fqfield = FullQualifiedField(self.field.to, rel_id, related_name)
            else:
                assert isinstance(rel_id, FullQualifiedId)
                fqfield = FullQualifiedField(rel_id.collection, rel_id.id, related_name)
            relations[fqfield] = rel_element
        return relations

    def prepare_result_to_fqid(
        self,
        add: Union[Set[int], Set[FullQualifiedId]],
        remove: Union[Set[int], Set[FullQualifiedId]],
        rels: Union[Dict[int, Any], Dict[FullQualifiedId, Any]],
        related_name: str,
    ) -> Relations:
        """
        Final method to prepare the result i. e. the new value of the relation field.

        Here the new value contains one or more FQIDs.
        """
        relations: Relations = {}
        for rel_id, rel in sorted(rels.items(), key=lambda item: item[0]):
            new_value: Optional[Union[FullQualifiedId, List[FullQualifiedId]]]
            if rel_id in add:
                value_to_be_added = FullQualifiedId(
                    collection=self.field.own_collection, id=self.id
                )
                if self.type in ("1:1", "m:1"):
                    if rel.get(related_name) is None:
                        new_value = value_to_be_added
                    else:
                        if isinstance(rel_id, int):
                            msg = KEYSEPARATOR.join(
                                (str(self.field.to), str(rel_id), related_name)
                            )
                        else:
                            msg = KEYSEPARATOR.join((str(rel_id), related_name))
                        message = (
                            f"You can not set {msg} in to a new value because this "
                            "field is not empty."
                        )
                        raise ActionException(message)
                else:
                    assert self.type in ("1:m", "m:n")
                    new_value = rel.get(related_name, []) + [value_to_be_added]
                rel_element = RelationsElement(
                    type="add", value=new_value, modified_element=value_to_be_added
                )
            else:
                assert rel_id in remove
                value_to_be_removed = FullQualifiedId(
                    collection=self.field.own_collection, id=self.id
                )
                if self.type in ("1:1", "m:1"):
                    new_value = None
                else:
                    assert self.type in ("1:m", "m:n")
                    new_value = rel[related_name]
                    assert isinstance(new_value, list)
                    new_value.remove(value_to_be_removed)
                rel_element = RelationsElement(
                    type="remove", value=new_value, modified_element=value_to_be_removed
                )
            if isinstance(rel_id, int):
                assert isinstance(self.field.to, Collection)
                fqfield = FullQualifiedField(self.field.to, rel_id, related_name)
            else:
                assert isinstance(rel_id, FullQualifiedId)
                fqfield = FullQualifiedField(rel_id.collection, rel_id.id, related_name)
            relations[fqfield] = rel_element
        return relations

    def prepare_result_template_field(
        self, result_structured_field: Relations, related_name: str, ids: List[int]
    ) -> Relations:
        """
        We also have to update the raw template field.

        TODO: This seems very hacky, maybe find a cleaner way to unify the field handling.
        """
        assert isinstance(self.field.to, Collection)
        response = self.datastore.get_many(
            get_many_requests=[
                GetManyRequest(
                    self.field.to, ids, mapped_fields=[self.field.related_name]
                )
            ],
            lock_result=True,
        )
        db_rels = response.get(self.field.to, {})
        result_template_field: Relations = {}
        for fqfield, rel_update in result_structured_field.items():
            assert isinstance(self.reverse_field, BaseTemplateField)
            match = re.match(self.reverse_field.get_regex(), related_name)
            if not match:
                raise ActionException(
                    "Structured field has invalid format: " + related_name
                )
            replacement = self.reverse_field.get_replacement(related_name)
            current_value = db_rels[fqfield.id].get(self.field.related_name, [])
            if (self.type in ("1:1", "m:1") and rel_update["value"] is None) or (
                self.type in ("1:m", "m:n") and rel_update["value"] == []
            ):
                # The field was emptied, so we have to remove the replacement.
                current_value.remove(replacement)
                rel_element = RelationsElement(
                    type="remove", value=current_value, modified_element=replacement
                )
            elif rel_update["type"] == "add" and (
                self.type in ("1:1", "m:1")
                or (
                    self.type in ("1:m", "m:n")
                    and isinstance(rel_update["value"], List)
                    and len(rel_update["value"]) == 1
                )
            ):
                # The replacement was added just now, so we have to add it to the template field.
                rel_element = RelationsElement(
                    type="add",
                    value=current_value + [replacement],
                    modified_element=replacement,
                )
            else:
                # Nothing to do, replacement already existed and still exists. Skip.
                continue
            result_template_field[
                FullQualifiedField(
                    fqfield.collection, fqfield.id, self.field.related_name
                )
            ] = rel_element
        return result_template_field
