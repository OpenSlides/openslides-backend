from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import fastjsonschema
from mypy_extensions import TypedDict

from ..models.base import Model
from ..models.fields import RelationMixin
from ..services.datastore.interface import Datastore
from ..shared.exceptions import ActionException, PermissionDenied
from ..shared.interfaces import Event, Permission, WriteRequestElement
from ..shared.patterns import FullQualifiedId
from ..shared.typing import ModelMap
from .action_interface import ActionPayload
from .relations import Relations, RelationsHandler

DataSetElement = TypedDict(
    "DataSetElement",
    {"instance": Dict[str, Any], "new_id": int, "relations": Relations},
)
DataSet = TypedDict(
    "DataSet", {"data": Any, "agenda_items": Iterable[DataSetElement]}, total=False
)


class SchemaProvider(type):
    """
    Metaclass to provide pre-compiled JSON schemas for faster validation.
    """

    def __new__(cls, name, bases, attrs):  # type: ignore
        schema = attrs.get("schema")
        if schema is not None:
            attrs["schema_validator"] = fastjsonschema.compile(schema)
        return super().__new__(cls, name, bases, attrs)


class BaseAction:  # pragma: no cover
    """
    Abstract base class for an action.
    """

    permission: Permission
    database: Datastore
    user_id: int


class Action(BaseAction, metaclass=SchemaProvider):
    """
    Base class for an action.
    """

    model: Model
    schema: Dict
    schema_validator: Callable[[ActionPayload], None]

    def __init__(
        self,
        name: str,
        permission: Permission,
        database: Datastore,
        additional_relation_models: ModelMap = {},
    ) -> None:
        self.name = name
        self.permission = permission
        self.database = database
        self.additional_relation_models = additional_relation_models

    def perform(
        self, payload: ActionPayload, user_id: int
    ) -> Iterable[WriteRequestElement]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.validate(payload)
        self.check_permissions(payload)
        dataset = self.prepare_dataset(payload)
        return self.create_write_request_elements(dataset)

    def validate(self, payload: ActionPayload) -> None:
        """
        Validates action payload according to schema class attribute.
        """
        try:
            type(self).schema_validator(payload)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

    def check_permissions(self, payload: ActionPayload) -> None:
        """
        Checks permission by requesting permission service.
        """
        if not self.permission.check_action(self.user_id, self.name, payload):
            raise PermissionDenied(
                f"You are not allowed to perform action {self.name}."
            )

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

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        """
        Takes dataset and creates write request elements that can be sent to event
        store.

        By default it calls self.create_instance_write_request_element and uses
        get_relations_updates() for relations.
        """
        for element in dataset["data"]:
            instance_write_request_element = self.create_instance_write_request_element(
                element
            )
            for relation in self.get_relations_updates(element):
                instance_write_request_element = merge_write_request_elements(
                    (instance_write_request_element, relation)
                )
            yield instance_write_request_element

    def create_instance_write_request_element(
        self, element: Any
    ) -> WriteRequestElement:
        """
        Creates a write request element for one instance of the current model.
        """
        raise NotImplementedError

    def get_relations_updates(
        self, element: Any, model: Model = None
    ) -> Iterable[WriteRequestElement]:
        """
        Creates write request elements (with update events) for all relations.
        """
        if model is None:
            model = self.model
        for fqfield, data in element["relations"].items():
            event = Event(
                type="update",
                fqid=FullQualifiedId(fqfield.collection, fqfield.id),
                fields={fqfield.field: data["value"]},
            )
            if data["type"] == "add":
                info_text = f"Object attached to {model}"
            else:
                # data["type"] == "remove"
                info_text = f"Object attachment to {model} reset"
            yield WriteRequestElement(
                events=[event],
                information={
                    FullQualifiedId(fqfield.collection, fqfield.id): [info_text]
                },
                user_id=self.user_id,
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
                additional_relation_models=self.additional_relation_models,
            )
            result = handler.perform()
            relations.update(result)
        return relations


class DummyAction(Action):
    """
    Dummy action that shows, that his action should to be implemented next.
    """

    is_dummy = True

    def perform(
        self, payload: ActionPayload, user_id: int
    ) -> Iterable[WriteRequestElement]:
        raise NotImplementedError(
            "This action has to be implemented but is still missing."
        )


def merge_write_request_elements(
    write_request_elements: Iterable[WriteRequestElement],
) -> WriteRequestElement:
    """
    Merges the given write request elements to one big write request element.
    """
    events: List[Event] = []
    information: Dict[FullQualifiedId, List[str]] = {}
    user_id: Optional[int] = None
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
    if user_id is None:
        raise ValueError("At least one of the given user ids must not be None.")
    return WriteRequestElement(events=events, information=information, user_id=user_id)
