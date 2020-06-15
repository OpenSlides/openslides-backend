from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from fastjsonschema import JsonSchemaException  # type: ignore
from mypy_extensions import TypedDict

from ..models.base import Model
from ..models.fields import RelationMixin
from ..services.datastore.interface import Datastore
from ..shared.exceptions import ActionException
from ..shared.interfaces import Event, Permission, WriteRequestElement
from ..shared.patterns import FullQualifiedId
from .actions_interface import ActionPayload
from .relations import Relations, RelationsHandler

DataSet = TypedDict("DataSet", {"data": Any})


class BaseAction:  # pragma: no cover
    """
    Abstract base class for actions.
    """

    permission: Permission
    database: Datastore
    user_id: int


class Action(BaseAction):
    """
    Base class for actions.
    """

    model: Model

    schema: Callable[[ActionPayload], None]

    def __init__(self, permission: Permission, database: Datastore) -> None:
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
        for element in dataset["data"]:
            element_write_request_element = self.create_instance_write_request_element(
                element
            )
            for relation in self.get_relations_updates(element):
                element_write_request_element = merge_write_request_elements(
                    (element_write_request_element, relation)
                )
            yield element_write_request_element

    def create_instance_write_request_element(
        self, element: Any
    ) -> WriteRequestElement:
        """
        Creates a write request element for one instance of the current model.
        """
        raise NotImplementedError

    def get_relations_updates(self, element: Any) -> Iterable[WriteRequestElement]:
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
                locked_fields={},
            )

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
