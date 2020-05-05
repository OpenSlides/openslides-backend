from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

from fastjsonschema import JsonSchemaException  # type: ignore
from mypy_extensions import TypedDict

from ..models.base import Model
from ..models.fields import RelationMixin
from ..shared.exceptions import ActionException
from ..shared.interfaces import Database, Event, Permission, WriteRequestElement
from ..shared.patterns import FullQualifiedField, FullQualifiedId
from .actions_interface import ActionPayload

DataSet = TypedDict("DataSet", {"position": int, "data": Any})
RelationsElement = TypedDict(
    "RelationsElement", {"type": str, "value": Union[Optional[int], List[int]]}
)
Relations = Dict[FullQualifiedField, RelationsElement]


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

        This can only be used of payload is a list.
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
        add: Set[int]
        remove: Set[int]
        relations: Relations = {}

        for field_name, field, is_reverse in relation_fields:
            if not is_reverse:
                # Common relation case: 1:m or m:n or 1:1 case.

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
                    add, remove = self.relation_diff_to_many(
                        model, id, field_name, field, rel_ids
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
                for rel_id, rel in rels.items():
                    if rel_id in add:
                        value_to_be_added: Union[int, FullQualifiedId]
                        if field.generic_relation:
                            value_to_be_added = FullQualifiedId(
                                collection=field.own_collection, id=id
                            )
                        else:
                            value_to_be_added = id
                        rel_element = RelationsElement(
                            type="add",
                            value=rel.get(related_name, []) + [value_to_be_added],
                        )
                    else:
                        # ref_id in remove
                        value_to_be_removed: Union[int, FullQualifiedId]
                        if field.generic_relation:
                            value_to_be_removed = FullQualifiedId(
                                collection=field.own_collection, id=id
                            )
                        else:
                            value_to_be_removed = id
                        new_value = rel[related_name]
                        new_value.remove(value_to_be_removed)
                        rel_element = RelationsElement(type="remove", value=new_value,)
                    fqfield = FullQualifiedField(field.to, rel_id, related_name)
                    relations[fqfield] = rel_element

            else:
                # Reverse relation case: m:n, m:1 or 1:1

                # Prepare new relation ids
                value = obj.get(field_name)

                if field.type == "m:n":
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
                        add, remove = self.relation_diff_to_many(
                            model, id, field_name, field, rel_ids
                        )

                    # Get related models from database
                    if field.generic_relation:
                        raise NotImplementedError(
                            "Generic relation case is not implemented yet."
                        )
                    rels, position = self.database.getMany(
                        field.own_collection,
                        list(add | remove),
                        mapped_fields=[field.own_field_name],
                    )
                    self.set_min_position(position)

                    # Prepare result which contains relations elements for add case and
                    # for remove case
                    for rel_id, rel in rels.items():
                        if rel_id in add:
                            rel_element = RelationsElement(
                                type="add",
                                value=rel.get(field.own_field_name, []) + [id],
                            )
                        else:
                            # ref_id in remove
                            new_value = rel[field.own_field_name]
                            new_value.remove(id)
                            rel_element = RelationsElement(
                                type="remove", value=new_value,
                            )
                        fqfield = FullQualifiedField(
                            field.own_collection, rel_id, field.own_field_name
                        )
                        relations[fqfield] = rel_element

                else:
                    assert field.type in ("1:m", "1:1")
                    # Note: 1:m means m:1 here because we are in reverse relation case
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
                        add, remove = self.relation_diff_to_one(
                            model, id, field_name, field, rel_ids
                        )

                    # Get related models from database
                    if field.generic_relation:
                        rels = {}
                        for related_model_fqid in list(add | remove):
                            related_model, position = self.database.get(
                                related_model_fqid, mapped_fields=[field.own_field_name]
                            )
                            self.set_min_position(position)
                            rels[related_model_fqid] = related_model
                    else:
                        rels, position = self.database.getMany(
                            field.own_collection,
                            list(add | remove),
                            mapped_fields=[field.own_field_name],
                        )
                        self.set_min_position(position)

                    # Prepare result which contains relations elements for add case and
                    # for remove case
                    for rel_id, rel in rels.items():
                        if rel_id in add:
                            if rel.get(field.own_field_name) is None:
                                rel_element = RelationsElement(type="add", value=id,)
                            else:
                                raise ActionException(
                                    f"You can not add {rel_id} to field {field_name} "
                                    "because related field is not empty."
                                )
                        else:
                            # ref_id in remove
                            if field.on_delete == "protect":
                                raise ActionException(
                                    f"You are not allowed to delete {model} {id} as "
                                    "long as there are some required related objects "
                                    f"(see {field_name})."
                                )
                            # else: field.on_delete == "set_null"
                            rel_element = RelationsElement(type="remove", value=None,)
                        if field.generic_relation:
                            fqfield = FullQualifiedField(
                                rel_id.collection, rel_id.id, field.own_field_name
                            )  # TODO: own_field_name is not guaranteed here
                        else:
                            fqfield = FullQualifiedField(
                                field.own_collection, rel_id, field.own_field_name
                            )
                        relations[fqfield] = rel_element

        return relations

    def relation_diff_to_many(
        self,
        model: Model,
        id: int,
        field_name: str,
        field: RelationMixin,
        rel_ids: List[int],
    ) -> Tuple[Set[int], Set[int]]:
        """
        Returns two sets of relation object ids. One with relation objects
        where the given object (represented by model and id) should be added
        and one with relation objects where it should be removed.

        This method is only for 1:n or m:n case.
        """
        # Fetch current object from database
        current_obj, position = self.database.get(
            FullQualifiedId(model.collection, id), mapped_fields=[field_name]
        )
        self.set_min_position(position)

        # Fetch current ids from relation field
        if field.type in ("1:m", "1:1"):
            current_id = current_obj.get(field_name)
            if current_id is None:
                current_ids = set()
            else:
                current_ids = set([current_id])
        else:
            assert field.type == "m:n"
            current_ids = set(current_obj.get(field_name, []))

        # Calculate and return add set and remove set
        new_ids = set(rel_ids)
        add = new_ids - current_ids
        remove = current_ids - new_ids
        return (add, remove)

    def relation_diff_to_one(
        self,
        model: Model,
        id: int,
        field_name: str,
        field: RelationMixin,
        rel_ids: List[int],
    ) -> Tuple[Set[int], Set[int]]:
        """
        Returns two sets of relation object ids. One with relation objects
        where the given object (represented by model and id) should be added
        and one with relation objects where it should be removed.

        This method is only for m:1 case.
        """
        # Fetch current object from database
        current_obj, position = self.database.get(
            FullQualifiedId(model.collection, id), mapped_fields=[field_name]
        )
        self.set_min_position(position)

        current_ids = set(current_obj.get(field_name, []))

        # Calculate and return add set and remove set
        new_ids = set(rel_ids)
        add = new_ids - current_ids
        remove = current_ids - new_ids
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
