from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from mypy_extensions import TypedDict

from ..models.base import Model
from ..models.fields import RelationMixin
from ..services.datastore.interface import GetManyRequest
from ..shared.exceptions import ActionException
from ..shared.patterns import Collection, FullQualifiedField, FullQualifiedId

RelationsElement = TypedDict(
    "RelationsElement",
    {
        "type": str,
        "value": Optional[
            Union[int, FullQualifiedId, List[int], List[FullQualifiedId]]
        ],
    },
)
Relations = Dict[FullQualifiedField, RelationsElement]


class RelationsHandler:
    """
    This class combines serveral methods to calculate changes of relation fields.

    There are the following distinctions:
        by type: 1:1, 1:m / m:1 or m:n
        by direction: common or reverse
        by field: normal field or with structured field
        by content: integer relation and generic relation (using a full qualified id)

    Therefor we have many cases this class has to handle (e. g. reverse relation
    m:n with structured field or common relation 1:m with generic relation)
    """

    def __init__(
        self,
        database: Any,  # TODO: Use a database connection here.
        model: Model,
        id: int,
        field: RelationMixin,
        field_name: str,
        obj: Dict[str, Any],
        is_reverse: bool = False,
        only_add: bool = False,
        only_remove: bool = False,
    ) -> None:
        self.database = database
        self.model = model
        self.id = id
        self.field = field
        self.field_name = field_name
        self.obj = obj
        self.is_reverse = is_reverse
        if only_add and only_remove:
            raise ValueError(
                "Do not set only_add and only_remove because this is contradictory."
            )
        self.only_add = only_add
        self.only_remove = only_remove
        self.type = self.field.type
        if self.type == "1:m" and self.is_reverse:
            # Switch 1:m to m:1 in reverse case.
            self.type = "m:1"

        # TODO: Implement this case.
        if self.field.generic_relation and self.is_reverse and self.type == "m:n":
            raise NotImplementedError

    def perform(self) -> Relations:
        rel_ids = self.prepare_new_relation_ids()
        related_name = self.get_related_name()
        target = self.field.own_collection if self.is_reverse else self.field.to

        add: Union[Set[int], Set[FullQualifiedId]]
        remove: Union[Set[int], Set[FullQualifiedId]]

        if self.field.generic_relation and self.is_reverse:
            rel_ids = cast(List[FullQualifiedId], rel_ids)
            add, remove = self.relation_diffs_fqid(rel_ids)
            rels = {}
            for related_model_fqid in list(add | remove):
                related_model = self.database.get(
                    related_model_fqid, mapped_fields=[related_name, "meta_position"]
                )
                rels[related_model_fqid] = related_model
        else:
            rel_ids = cast(List[int], rel_ids)
            add, remove = self.relation_diffs(rel_ids)
            response = self.database.get_many(
                [
                    GetManyRequest(
                        target,
                        list(add | remove),
                        mapped_fields=[related_name, "meta_position"],
                    )
                ]
            )
            # TODO: Check existance of fetched objects.
            rels = {}
            for fqid, related_model in response.items():
                rels[fqid.id] = related_model

        if self.field.generic_relation and not self.is_reverse:
            return self.prepare_result_to_fqid(add, remove, rels, target, related_name)
        return self.prepare_result_to_id(add, remove, rels, target, related_name)

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
            if not self.is_reverse:
                related_name = self.field.related_name
            else:
                related_name = self.field.own_field_name
        else:
            if self.is_reverse:
                raise NotImplementedError
            # Fetch current db instance with structured_relation field.
            db_instance = self.database.get(
                fqid=FullQualifiedId(self.model.collection, id=self.id),
                mapped_fields=[self.field.structured_relation],
            )
            if db_instance.get(self.field.structured_relation) is None:
                raise ValueError(
                    f"The field {self.field.structured_relation} must not be empty in database."
                )
            related_name = self.field.related_name.replace(
                "$", str(db_instance.get(self.field.structured_relation))
            )
        return related_name

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
                mapped_fields=[self.field_name, "meta_position"],
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
                mapped_fields=[self.field_name, "meta_position"],
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
                collection, id = current_id.split("/")
                transformed_current_ids.add(
                    FullQualifiedId(Collection(collection), int(id))
                )

            # Calculate add set and remove set
            new_ids = set(rel_ids)
            add = new_ids - transformed_current_ids
            remove = transformed_current_ids - new_ids

        return add, remove

    def prepare_result_to_id(
        self,
        add: Union[Set[int], Set[FullQualifiedId]],
        remove: Union[Set[int], Set[FullQualifiedId]],
        rels: Union[Dict[int, Any], Dict[FullQualifiedId, Any]],
        target: Collection,
        related_name: str,
    ) -> Relations:
        relations: Relations = {}
        for rel_id, rel in sorted(rels.items(), key=lambda item: str(item[0])):
            new_value: Optional[Union[int, List[int]]]
            if rel_id in add:
                if self.field.type in ("1:1", "m:1"):
                    if rel.get(related_name) is None:
                        new_value = self.id
                    else:
                        raise ActionException(
                            f"You can not add {rel_id} to field {self.field_name} "
                            "because related field is not empty."
                        )
                else:
                    assert self.field.type in ("1:m", "m:n")
                    value_to_be_added = self.id
                    new_value = rel.get(related_name, []) + [value_to_be_added]
                rel_element = RelationsElement(type="add", value=new_value)
            else:
                assert rel_id in remove
                if self.is_reverse and self.field.on_delete == "protect":
                    # Hint: There is no on_delete behavior in common relation
                    # case so the reverse field is always nullable.
                    raise ActionException(
                        f"You are not allowed to delete {self.model} {self.id} as "
                        "long as there are some required related objects "
                        f"(see {self.field_name})."
                    )
                if self.field.type in ("1:1", "m:1"):
                    new_value = None
                else:
                    assert self.field.type in ("1:m", "m:n")
                    value_to_be_removed = self.id
                    new_value = rel[related_name]
                    assert isinstance(new_value, list)
                    new_value.remove(value_to_be_removed)
                rel_element = RelationsElement(type="remove", value=new_value)
            if isinstance(rel_id, int):
                fqfield = FullQualifiedField(target, rel_id, related_name)
            else:
                assert isinstance(rel_id, FullQualifiedId)
                fqfield = FullQualifiedField(target, rel_id.id, related_name)
            relations[fqfield] = rel_element
        return relations

    def prepare_result_to_fqid(
        self,
        add: Union[Set[int], Set[FullQualifiedId]],
        remove: Union[Set[int], Set[FullQualifiedId]],
        rels: Union[Dict[int, Any], Dict[FullQualifiedId, Any]],
        target: Collection,
        related_name: str,
    ) -> Relations:
        relations: Relations = {}
        for rel_id, rel in sorted(rels.items(), key=lambda item: item[0]):
            new_value: Optional[Union[FullQualifiedId, List[FullQualifiedId]]]
            if rel_id in add:
                if self.field.type in ("1:1", "m:1"):
                    if rel.get(related_name) is None:
                        new_value = FullQualifiedId(
                            collection=self.field.own_collection, id=self.id
                        )
                    else:
                        raise ActionException(
                            f"You can not add {rel_id} to field {self.field_name} "
                            "because related field is not empty."
                        )
                else:
                    assert self.field.type in ("1:m", "m:n")
                    value_to_be_added = FullQualifiedId(
                        collection=self.field.own_collection, id=self.id
                    )
                    new_value = rel.get(related_name, []) + [value_to_be_added]
                rel_element = RelationsElement(type="add", value=new_value)
            else:
                assert rel_id in remove
                if self.is_reverse and self.field.on_delete == "protect":
                    # Hint: There is no on_delete behavior in common relation
                    # case so the reverse field is always nullable.
                    raise ActionException(
                        f"You are not allowed to delete {self.model} {self.id} as "
                        "long as there are some required related objects "
                        f"(see {self.field_name})."
                    )
                if self.field.type in ("1:1", "m:1"):
                    new_value = None
                else:
                    assert self.field.type in ("1:m", "m:n")
                    value_to_be_removed = FullQualifiedId(
                        collection=self.field.own_collection, id=self.id
                    )
                    new_value = rel[related_name]
                    assert isinstance(new_value, list)
                    new_value.remove(value_to_be_removed)
                rel_element = RelationsElement(type="remove", value=new_value)
            if isinstance(rel_id, int):
                fqfield = FullQualifiedField(target, rel_id, related_name)
            else:
                assert isinstance(rel_id, FullQualifiedId)
                fqfield = FullQualifiedField(target, rel_id.id, related_name)
            relations[fqfield] = rel_element
        return relations
