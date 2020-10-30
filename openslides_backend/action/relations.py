from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from mypy_extensions import TypedDict

from ..models.base import Model, model_registry
from ..models.fields import (
    BaseRelationField,
    GenericRelationField,
    GenericRelationListField,
    OnDelete,
    RelationField,
    RelationListField,
    TemplateRelationField,
    TemplateRelationListField,
)
from ..services.datastore.interface import GetManyRequest, PartialModel
from ..shared.exceptions import ActionException
from ..shared.patterns import (
    KEYSEPARATOR,
    Collection,
    FullQualifiedField,
    FullQualifiedId,
    string_to_fqid,
)
from ..shared.typing import ModelMap

RelationsElement = TypedDict(
    "RelationsElement",
    {
        "type": str,
        "value": Optional[
            Union[int, FullQualifiedId, List[int], List[FullQualifiedId]]
        ],
        "modified_element": Union[int, FullQualifiedId],
    },
)
Relations = Dict[FullQualifiedField, RelationsElement]


class RelationsHandler:
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
        database: Any,  # TODO: Use a database connection here.
        model: Model,
        id: int,
        field: BaseRelationField,
        field_name: str,
        obj: Dict[str, Any],
        only_add: bool = False,
        only_remove: bool = False,
        additional_relation_models: ModelMap = {},
    ) -> None:
        self.database = database
        self.model = model
        self.id = id
        self.field = field
        self.field_name = field_name
        self.obj = obj
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
        return model_registry[reverse_collection]().get_field(related_name)

    def get_field_type(self) -> str:
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
        rel_ids = self.prepare_new_relation_ids()
        related_name = self.get_related_name()

        if isinstance(self.field, TemplateRelationField) or isinstance(
            self.field, TemplateRelationListField
        ):
            if self.field_name.find("$_") > -1 or self.field_name[-1] == "$":
                raise ValueError(
                    "You can not handle raw template fields here. Use then with "
                    "populated replacements."
                )

        add: Union[Set[int], Set[FullQualifiedId]]
        remove: Union[Set[int], Set[FullQualifiedId]]
        rels: Union[Dict[int, PartialModel], Dict[FullQualifiedId, PartialModel]]

        if isinstance(self.field, GenericRelationField) or isinstance(
            self.field, GenericRelationListField
        ):
            assert isinstance(self.field.to, list)
            rel_ids = cast(List[FullQualifiedId], rel_ids)
            add, remove = self.relation_diffs_fqid(rel_ids)
            fq_rels = {}
            for related_model_fqid in list(add | remove):
                if related_model_fqid.collection not in self.field.to:
                    raise RuntimeError(
                        "You try to change a generic relation field using foreign collections that are not available."
                    )
                if related_model_fqid in self.additional_relation_models:
                    related_model = {
                        related_name: self.additional_relation_models[
                            related_model_fqid
                        ].get(related_name)
                    }
                else:
                    related_model = self.database.get(
                        related_model_fqid,
                        mapped_fields=[related_name],
                        lock_result=True,
                    )
                fq_rels[related_model_fqid] = related_model
            rels = fq_rels
        else:
            assert isinstance(self.field.to, Collection)
            rel_ids = cast(List[int], rel_ids)
            add, remove = self.relation_diffs(rel_ids)
            ids = list(add | remove)
            response = self.database.get_many(
                get_many_requests=[
                    GetManyRequest(self.field.to, ids, mapped_fields=[related_name])
                ],
                lock_result=True,
            )
            # TODO: Check if the datastore really sends such an empty response.
            id_rels = response[self.field.to] if self.field.to in response else {}

            # Switch type of values that represent a FQID
            # only in non-reverse generic relation case.
            if self.field.generic_relation:
                for rel_item in id_rels.values():
                    related_field_value = rel_item.get(related_name)
                    if related_field_value is not None:
                        if self.type in ("1:1", "m:1"):
                            rel_item[related_name] = string_to_fqid(related_field_value)
                        else:
                            assert self.type in ("1:m", "m:n")
                            new_related_field_value = []
                            for value_item in related_field_value:
                                new_related_field_value.append(
                                    string_to_fqid(value_item)
                                )
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

        if self.field.generic_relation:
            return self.prepare_result_to_fqid(add, remove, rels, related_name)
        return self.prepare_result_to_id(add, remove, rels, related_name)

    def prepare_new_relation_ids(self) -> Union[List[int], List[FullQualifiedId]]:
        value = self.obj.get(self.field_name)
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
        if self.field.structured_relation is None:
            related_name = self.field.related_name
        else:
            replacement = self.search_structured_relation(
                list(self.field.structured_relation), self.model.collection, self.id
            )
            related_name = self.field.related_name.replace("$", replacement)
        return related_name

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
        value = self.obj.get(field_name)
        if value is None:
            db_instance = self.database.get(
                fqid=FullQualifiedId(collection, id),
                mapped_fields=[field_name],
            )
            value = db_instance.get(field_name)
        if value is None:
            raise ValueError(
                f"The field {field_name} for {collection} must not be empty in database."
            )
        if structured_relation:
            new_collection = model_registry[collection]().get_field(field_name).to
            assert isinstance(new_collection, Collection)
            return self.search_structured_relation(
                structured_relation, new_collection, value
            )
        return str(value)

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
            # We have to compare with the current database state.

            # Retrieve current object from database
            current_obj = self.database.get(
                FullQualifiedId(self.model.collection, self.id),
                mapped_fields=[self.field_name],
                lock_result=True,
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
            # We have to compare with the current database state.

            # Retrieve current object from database
            current_obj = self.database.get(
                FullQualifiedId(self.model.collection, self.id),
                mapped_fields=[self.field_name],
                lock_result=True,
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
                transformed_current_ids.add(string_to_fqid(current_id))

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
                if (
                    self.type in ("1:1", "m:1")
                    and self.reverse_field.on_delete == OnDelete.PROTECT
                ):
                    # Hint: There is no on_delete behavior in m:n cases. The reverse
                    # field is always nullable. We just modifiy the related field list.
                    raise ActionException(
                        f"You are not allowed to delete {self.model} {self.id} as "
                        "long as there are some required related objects."
                    )
                if self.type in ("1:1", "m:1"):
                    new_value = None
                else:
                    assert self.type in ("1:m", "m:n")
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
                if (
                    self.type in ("1:1", "m:1")
                    and self.reverse_field.on_delete == OnDelete.PROTECT
                ):
                    # Hint: There is no on_delete behavior in m:n cases. The reverse
                    # field is always nullable. We just modifiy the related field list.
                    raise ActionException(
                        f"You are not allowed to delete {self.model} {self.id} as "
                        "long as there are some required related objects."
                    )
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
