from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

from fastjsonschema import JsonSchemaException  # type: ignore
from mypy_extensions import TypedDict

from ..models.base import Model
from ..models.fields import RelationMixin
from ..shared.exceptions import ActionException
from ..shared.interfaces import Database, Event, Permission, WriteRequestElement
from ..shared.patterns import Collection, FullQualifiedField, FullQualifiedId
from .actions_interface import ActionPayload
from .relations import Relations, RelationsElement, RelationsHandler

DataSet = TypedDict("DataSet", {"position": int, "data": Any})


class BaseAction:  # pragma: no cover
    """
    Abstract base class for actions.
    """

    permission: Permission
    database: Database
    user_id: int
    position: int

    def set_min_position(self, position: int) -> None:
        ...


class Action(BaseAction):
    """
    Base class for actions.
    """

    model: Model

    schema: Callable[[ActionPayload], None]

    position = 0

    def __init__(self, permission: Permission, database: Database) -> None:
        self.permission = permission
        self.database = database

    def perform(
        self, payload: ActionPayload, user_id: int
    ) -> Iterable[WriteRequestElement]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.validate(payload)
        dataset = self.prepare_dataset(payload)
        self.check_permission_on_dataset(dataset)
        return self.create_write_request_elements(dataset)

    def validate(self, payload: ActionPayload) -> None:
        """
        Validates action payload according to schema class attribute.
        """
        try:
            type(self).schema(payload)
        except JsonSchemaException as exception:
            raise ActionException(exception.message)

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        """
        Prepares dataset from payload. Also fires all necessary database
        queries.
        """
        raise NotImplementedError

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates one instance of the payload. This can be overridden by custom
        action classes.

        This can only be used if payload is a list.
        """
        return instance

    def check_permission_on_dataset(self, dataset: DataSet) -> None:
        """
        Checks permission in the middle of the action according to dataset. Can
        be used for extra checks. Just passes at default.
        """
        pass

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        """
        Takes dataset and creates write request elements that can be sent to event
        store.

        By default it calls self.create_element_write_request_element and uses
        get_relations_updates() for relations.
        """
        position = dataset["position"]
        for element in dataset["data"]:
            element_write_request_element = self.create_instance_write_request_element(
                position, element
            )
            for relation in self.get_relations_updates(position, element):
                element_write_request_element = merge_write_request_elements(
                    (element_write_request_element, relation)
                )
            yield element_write_request_element

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        """
        Creates a write request element for one instance of the current model.
        """
        raise NotImplementedError

    def get_relations_updates(
        self, position: int, element: Any
    ) -> Iterable[WriteRequestElement]:
        """
        Creates write request elements (with update events) for all relations.
        """
        for fqfield, data in element["relations"].items():
            event = Event(
                type="update",
                fqid=FullQualifiedId(fqfield.collection, fqfield.id),
                fields={fqfield.field: data["value"]},
            )
            if data["type"] == "add":
                info_text = f"Object attached to {self.model}"
            else:
                # data["type"] == "remove"
                info_text = f"Object attachment to {self.model} reset"
            yield WriteRequestElement(
                events=[event],
                information={
                    FullQualifiedId(fqfield.collection, fqfield.id): [info_text]
                },
                user_id=self.user_id,
                locked_fields={fqfield: position},
            )

    def set_min_position(self, position: int) -> None:
        """
        Sets self.position to the new value position if this value is smaller
        than the old one. Sets it if it is the first call.
        """
        if self.position == 0:
            self.position = position
        else:
            self.position = min(position, self.position)

    def get_relations(
        self,
        model: Model,
        id: int,
        obj: Dict[str, Any],
        relation_fields: Iterable[Tuple[str, RelationMixin, bool]],
        shortcut: bool = False,
    ) -> Relations:
        """
        Updates (reverse) relations of the given model for the given fields. Use
        this method in prepare_dataset method.

        If shortcut is True, we assume a create case. That means that all
        relations are added.
        """
        relations: Relations = {}
        for field_name, field, is_reverse in relation_fields:
            handler = RelationsHandler(
                self.database,
                self.set_min_position,
                model,
                id,
                field,
                field_name,
                obj,
                is_reverse,
                only_add=shortcut,
                only_remove=False,
            )
            result = handler.perform()
            relations.update(result)
        return relations

    def get_relations_common_relation_case(
        self,
        model: Model,
        id: int,
        obj: Dict[str, Any],
        field: RelationMixin,
        field_name: str,
        shortcut: bool = False,
    ) -> Relations:
        """
        Helper function #1.1 to get_relations method.

        Common relation cases 1:1, 1:m or m:n with integer id relation.
        """
        add: Set[int]
        remove: Set[int]
        relations: Relations = {}

        # Prepare new relation ids
        value = obj.get(field_name)
        if value is None:
            rel_ids = []
        else:
            if field.type in ("1:m", "1:1"):
                # We simulate a list of new values in these cases so
                # we can reuse the code here.
                rel_ids = [value]
            else:
                assert field.type == "m:n"
                rel_ids = value

        # Parse which relation ids should be added and which should be
        # removed in related model.
        if shortcut:
            add = set(rel_ids)
            remove = set()
        else:
            add, remove = self.relation_diff_with_id(
                model, id, field_name, field, rel_ids, field.type == "m:n",
            )
        if field.structured_relation is None:
            related_name = field.related_name
        else:
            # Fetch current db instance with structured_relation field.
            db_instance, position = self.database.get(
                fqid=FullQualifiedId(model.collection, id=obj["id"]),
                mapped_fields=[field.structured_relation],
            )
            self.set_min_position(position)
            if db_instance.get(field.structured_relation) is None:
                raise ValueError(
                    f"The field {field.structured_relation} must not be empty in database."
                )
            related_name = field.related_name.replace(
                "$", str(db_instance.get(field.structured_relation))
            )

        # Get related models from database
        rels, position = self.database.getMany(
            field.to, list(add | remove), mapped_fields=[related_name],
        )
        self.set_min_position(position)

        # Prepare result which contains relations elements for add case and
        # for remove case
        for rel_id, rel in sorted(rels.items(), key=lambda item: item[0]):
            new_value: Optional[Union[int, List[int]]]
            if rel_id in add:
                if field.type == "1:1":
                    if rel.get(field.related_name) is None:
                        new_value = id
                    else:
                        raise ActionException(
                            f"You can not add {rel_id} to field {field_name} "
                            "because related field is not empty."
                        )
                else:
                    assert field.type in ("1:m", "m:n")
                    value_to_be_added = id
                    new_value = rel.get(related_name, []) + [value_to_be_added]
                rel_element = RelationsElement(type="add", value=new_value)
            else:
                assert rel_id in remove
                if field.type == "1:1":
                    # Hint: There is no on_delete behavior like in reverse
                    # relation case so the reverse field is always nullable
                    new_value = None
                else:
                    assert field.type in ("1:m", "m:n")
                    value_to_be_removed = id
                    new_value = rel[related_name]
                    assert isinstance(new_value, list)
                    new_value.remove(value_to_be_removed)
                rel_element = RelationsElement(type="remove", value=new_value)
            fqfield = FullQualifiedField(field.to, rel_id, related_name)
            relations[fqfield] = rel_element

        return relations

    def get_relations_common_relation_case_generic(
        self,
        model: Model,
        id: int,
        obj: Dict[str, Any],
        field: RelationMixin,
        field_name: str,
        shortcut: bool = False,
    ) -> Relations:
        """
        Helper function #1.2 to get_relations method.

        Common relation cases 1:1, 1:m or m:n with generic relation.
        """
        add: Set[int]
        remove: Set[int]
        relations: Relations = {}

        # Prepare new relation ids
        value = obj.get(field_name)
        if value is None:
            rel_ids = []
        else:
            if field.type in ("1:m", "1:1"):
                # We simulate a list of new values in these cases so
                # we can reuse the code here.
                rel_ids = [value]
            else:
                assert field.type == "m:n"
                rel_ids = value

        # Parse which relation ids should be added and which should be
        # removed in related model.
        if shortcut:
            add = set(rel_ids)
            remove = set()
        else:
            add, remove = self.relation_diff_with_id(
                model, id, field_name, field, rel_ids, field.type == "m:n",
            )
        if field.structured_relation is None:
            related_name = field.related_name
        else:
            # Fetch current db instance with structured_relation field.
            db_instance, position = self.database.get(
                fqid=FullQualifiedId(model.collection, id=obj["id"]),
                mapped_fields=[field.structured_relation],
            )
            self.set_min_position(position)
            if db_instance.get(field.structured_relation) is None:
                raise ValueError(
                    f"The field {field.structured_relation} must not be empty in database."
                )
            related_name = field.related_name.replace(
                "$", str(db_instance.get(field.structured_relation))
            )

        # Get related models from database
        rels, position = self.database.getMany(
            field.to, list(add | remove), mapped_fields=[related_name],
        )
        self.set_min_position(position)

        # Prepare result which contains relations elements for add case and
        # for remove case
        for rel_id, rel in sorted(rels.items(), key=lambda item: str(item[0])):
            new_value: Optional[Union[FullQualifiedId, List[FullQualifiedId]]]
            if rel_id in add:
                if field.type == "1:1":
                    if rel.get(field.related_name) is None:
                        new_value = FullQualifiedId(
                            collection=field.own_collection, id=id
                        )
                    else:
                        raise ActionException(
                            f"You can not add {rel_id} to field {field_name} "
                            "because related field is not empty."
                        )
                else:
                    assert field.type in ("1:m", "m:n")
                    value_to_be_added = FullQualifiedId(
                        collection=field.own_collection, id=id
                    )
                    new_value = rel.get(related_name, []) + [value_to_be_added]
                rel_element = RelationsElement(type="add", value=new_value)
            else:
                assert rel_id in remove
                if field.type == "1:1":
                    # Hint: There is no on_delete behavior like in reverse
                    # relation case so the reverse field is always nullable
                    new_value = None
                else:
                    assert field.type in ("1:m", "m:n")
                    value_to_be_removed = FullQualifiedId(
                        collection=field.own_collection, id=id
                    )
                    new_value = rel[related_name]
                    assert isinstance(new_value, list)
                    new_value.remove(value_to_be_removed)
                rel_element = RelationsElement(type="remove", value=new_value)
            fqfield = FullQualifiedField(field.to, rel_id, related_name)
            relations[fqfield] = rel_element

        return relations

    def get_relations_reverse_relation_case_many_to_many(
        self,
        model: Model,
        id: int,
        obj: Dict[str, Any],
        field: RelationMixin,
        field_name: str,
        shortcut: bool = False,
    ) -> Relations:
        """
        Helper function #2.1.1 to get_relations method.

        Reverse relation case m:n with integer id relation.
        """
        add: Set[int]
        remove: Set[int]
        relations: Relations = {}

        assert field.type == "m:n"

        # Prepare new relation ids
        value = obj.get(field_name)
        if value is None:
            rel_ids = []
        else:
            rel_ids = value

        # Parse which relation ids should be added and which should be
        # removed in related model.
        if shortcut:
            add = set(rel_ids)
            remove = set()
        else:
            add, remove = self.relation_diff_with_id(
                model, id, field_name, field, rel_ids, field.type == "m:n",
            )

        # Get related models from database
        rels, position = self.database.getMany(
            field.own_collection,
            list(add | remove),
            mapped_fields=[field.own_field_name],
        )
        self.set_min_position(position)

        # Prepare result which contains relations elements for add case and
        # for remove case
        for rel_id, rel in sorted(rels.items(), key=lambda item: item[0]):
            new_value: List[int]
            if rel_id in add:
                new_value = rel.get(field.own_field_name, []) + [id]
                rel_element = RelationsElement(type="add", value=new_value)
            else:
                assert rel_id in remove
                new_value = rel[field.own_field_name]
                new_value.remove(id)
                rel_element = RelationsElement(type="remove", value=new_value)
            fqfield = FullQualifiedField(
                field.own_collection, rel_id, field.own_field_name
            )
            relations[fqfield] = rel_element
        return relations

    # def get_relations_reverse_relation_case_many_to_many_generic(...)  # TODO: Add case #2.1.2 m:n generic

    def get_relations_reverse_relation_case_x_to_one(
        self,
        model: Model,
        id: int,
        obj: Dict[str, Any],
        field: RelationMixin,
        field_name: str,
        shortcut: bool = False,
    ) -> Relations:
        """
        Helper function #2.2.1 to get_relations method.

        Reverse relation cases m:1 and 1:1 with integer id relation.
        """
        add: Set[int]
        remove: Set[int]
        relations: Relations = {}

        # Hint: 1:m means m:1 here because we are in reverse relation case.
        assert field.type in ("1:1", "1:m")

        # Prepare new relation ids
        value = obj.get(field_name)
        if value is None:
            rel_ids = []
        else:
            if field.type == "1:1":
                # We simulate a list of new values in this case so
                # we can reuse the code here.
                rel_ids = [value]
            else:
                rel_ids = value

        # Parse which relation ids should be added and which should be
        # removed in related model.
        if shortcut:
            add = set(rel_ids)
            remove = set()
        else:
            add, remove = self.relation_diff_with_id(
                model, id, field_name, field, rel_ids, field.type == "1:m",
            )

        # Get related models from database
        rels, position = self.database.getMany(
            field.own_collection,
            list(add | remove),
            mapped_fields=[field.own_field_name],
        )
        self.set_min_position(position)

        # Prepare result which contains relations elements for add case and
        # for remove case
        for rel_id, rel in sorted(rels.items(), key=lambda item: item[0]):
            if rel_id in add:
                if rel.get(field.own_field_name) is None:
                    rel_element = RelationsElement(type="add", value=id)
                else:
                    raise ActionException(
                        f"You can not add {rel_id} to field {field_name} "
                        "because related field is not empty."
                    )
            else:
                assert rel_id in remove
                if field.on_delete == "protect":
                    raise ActionException(
                        f"You are not allowed to delete {model} {id} as "
                        "long as there are some required related objects "
                        f"(see {field_name})."
                    )
                # else: field.on_delete == "set_null"
                rel_element = RelationsElement(type="remove", value=None)
            fqfield = FullQualifiedField(
                field.own_collection, rel_id, field.own_field_name
            )
            relations[fqfield] = rel_element

        return relations

    def get_relations_reverse_relation_case_x_to_one_generic(
        self,
        model: Model,
        id: int,
        obj: Dict[str, Any],
        field: RelationMixin,
        field_name: str,
        shortcut: bool = False,
    ) -> Relations:
        """
        Helper function #2.2.2 to get_relations method.

        Reverse relation cases m:1 and 1:1 with generic relation.
        """
        add: Set[FullQualifiedId]
        remove: Set[FullQualifiedId]
        relations: Relations = {}

        # Hint: 1:m means m:1 here because we are in reverse relation case.
        assert field.type in ("1:1", "1:m")

        # Prepare new relation ids
        value = obj.get(field_name)
        if value is None:
            rel_ids = []
        else:
            if field.type == "1:1":
                # We simulate a list of new values in this case so
                # we can reuse the code here.
                rel_ids = [value]
            else:
                rel_ids = value

        # Parse which relation ids should be added and which should be
        # removed in related model.
        if shortcut:
            add = set(rel_ids)
            remove = set()
        else:
            add, remove = self.relation_diff_with_fqid(
                model, id, field_name, field, rel_ids, field.type == "1:m",
            )

        # Get related models from database
        rels = {}
        for related_model_fqid in list(add | remove):
            related_model, position = self.database.get(
                related_model_fqid, mapped_fields=[field.own_field_name]
            )
            self.set_min_position(position)
            rels[related_model_fqid] = related_model

        # Prepare result which contains relations elements for add case and
        # for remove case
        for rel_id, rel in sorted(rels.items(), key=lambda item: str(item[0])):
            if rel_id in add:
                if rel.get(field.own_field_name) is None:
                    rel_element = RelationsElement(type="add", value=id)
                else:
                    raise ActionException(
                        f"You can not add {rel_id} to field {field_name} "
                        "because related field is not empty."
                    )
            else:
                assert rel_id in remove
                if field.on_delete == "protect":
                    raise ActionException(
                        f"You are not allowed to delete {model} {id} as "
                        "long as there are some required related objects "
                        f"(see {field_name})."
                    )
                # else: field.on_delete == "set_null"
                rel_element = RelationsElement(type="remove", value=None)
            fqfield = FullQualifiedField(
                rel_id.collection, rel_id.id, field.own_field_name
            )  # TODO: own_field_name is not guaranteed here
            relations[fqfield] = rel_element

        return relations

    def relation_diff_with_id(
        self,
        model: Model,
        id: int,
        field_name: str,
        field: RelationMixin,
        rel_ids: List[int],
        many_to_x: bool,
    ) -> Tuple[Set[int], Set[int]]:
        """
        Returns two sets of relation object ids. One with relation objects
        where the given object (represented by model and id) should be added
        and one with relation objects where it should be removed.

        This method is for relation case with integer id.
        """
        # Fetch current object from database
        current_obj, position = self.database.get(
            FullQualifiedId(model.collection, id), mapped_fields=[field_name]
        )
        self.set_min_position(position)

        # Fetch current ids from relation field
        if not many_to_x:
            # Means 1:1 or 1:m case
            current_id = current_obj.get(field_name)
            if current_id is None:
                current_ids = set()
            else:
                # Means m:1 or m:n case
                current_ids = set([current_id])
        else:
            current_ids = set(current_obj.get(field_name, []))

        # Calculate and return add set and remove set
        new_ids = set(rel_ids)
        add = new_ids - current_ids
        remove = current_ids - new_ids
        return (add, remove)

    def relation_diff_with_fqid(
        self,
        model: Model,
        id: int,
        field_name: str,
        field: RelationMixin,
        rel_ids: List[FullQualifiedId],
        many_to_x: bool,
    ) -> Tuple[Set[FullQualifiedId], Set[FullQualifiedId]]:
        """
        Returns two sets of relation object ids. One with relation objects
        where the given object (represented by model and id) should be added
        and one with relation objects where it should be removed.

        This method is relation case with generic id.
        """
        # Fetch current object from database
        current_obj, position = self.database.get(
            FullQualifiedId(model.collection, id), mapped_fields=[field_name]
        )
        self.set_min_position(position)

        # Fetch current ids from relation field
        if not many_to_x:
            # Means 1:1 or 1:m case
            current_id = current_obj.get(field_name)
            if current_id is None:
                current_ids = set()
            else:
                current_ids = set([current_id])
        else:
            # Means m:1 or m:n case
            current_ids = set(current_obj.get(field_name, []))

        # Transform str to FullQualifiedId
        transformed_current_ids = set()
        for current_id in current_ids:
            collection, id = current_id.split("/")
            transformed_current_ids.add(
                FullQualifiedId(Collection(collection), int(id))
            )

        # Calculate and return add set and remove set
        new_ids = set(rel_ids)
        add = new_ids - transformed_current_ids
        remove = transformed_current_ids - new_ids
        return (add, remove)


def merge_write_request_elements(
    write_request_elements: Iterable[WriteRequestElement],
) -> WriteRequestElement:
    """
    Merges the given write request elements to one big write request element.
    """
    events: List[Event] = []
    information: Dict[FullQualifiedId, List[str]] = {}
    user_id: Optional[int] = None
    locked_fields: Dict[Any, int] = {}
    for element in write_request_elements:
        events.extend(element["events"])
        for fqid, info_text in element["information"].items():
            if information.get(fqid) is None:
                information[fqid] = info_text
            else:
                information[fqid].extend(info_text)
        if user_id is None:
            user_id = element["user_id"]
        else:
            if user_id != element["user_id"]:
                raise ValueError(
                    "You can not merge two write request elements of different users."
                )
        for key, position in element["locked_fields"].items():
            if locked_fields.get(key) is None:
                locked_fields[key] = position
            else:
                locked_fields[key] = min(position, locked_fields[key])
    if user_id is None:
        raise
    return WriteRequestElement(
        events=events,
        information=information,
        user_id=user_id,
        locked_fields=locked_fields,
    )
