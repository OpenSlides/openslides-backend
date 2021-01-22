from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, Union

import fastjsonschema

from ..models.base import Model
from ..models.fields import (
    BaseGenericRelationField,
    BaseRelationField,
    BaseTemplateField,
    BaseTemplateRelationField,
)
from ..services.auth.interface import AuthenticationService
from ..services.datastore.interface import DatastoreService
from ..services.media.interface import MediaService
from ..services.permission.interface import PermissionService
from ..shared.exceptions import ActionException, PermissionDenied
from ..shared.interfaces.event import Event, EventType
from ..shared.interfaces.services import Services
from ..shared.interfaces.write_request_element import WriteRequestElement
from ..shared.patterns import FullQualifiedField, FullQualifiedId
from ..shared.typing import ModelMap
from .relations.relation_manager import RelationManager
from .util.typing import ActionPayload, ActionResponseResultsElement

PERMISSION_SPECIAL_CASE = "Special business logic"
GENERIC_PERMISSION = "Generic permission check"


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

    services: Services
    permission: PermissionService
    datastore: DatastoreService
    auth: AuthenticationService
    media: MediaService

    name: str
    model: Model
    user_id: int


class Action(BaseAction, metaclass=SchemaProvider):
    """
    Base class for an action.
    """

    schema: Dict
    schema_validator: Callable[[Dict[str, Any]], None]
    is_singular: bool = False
    internal: bool = False
    relation_manager: RelationManager

    modified_relation_fields: Dict[FullQualifiedField, Any]

    write_request_elements: List[
        Union[WriteRequestElement, ActionResponseResultsElement]
    ]

    def __init__(
        self,
        services: Services,
        datastore: DatastoreService,
        relation_manager: RelationManager,
        additional_relation_models: ModelMap = {},
    ) -> None:
        self.services = services
        self.permission = services.permission()
        self.auth = services.authentication()
        self.media = services.media()
        self.datastore = datastore
        self.relation_manager = relation_manager
        self.additional_relation_models = additional_relation_models
        self.modified_relation_fields = {}
        self.write_request_elements = []

    def perform(
        self, payload: ActionPayload, user_id: int
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.check_permissions(payload)
        for element in payload:
            self.validate_payload_element(element)

        instances = self.get_updated_instances(payload)
        for instance in instances:
            instance = self.base_update_instance(instance)

            instance_wre = self.create_write_request_elements(instance)
            self.write_request_elements.extend(instance_wre)

            relation_updates = self.handle_relation_updates(instance)
            self.write_request_elements.extend(relation_updates)

        yield from self.process_write_request_elements()

    def check_permissions(self, payload: ActionPayload) -> None:
        """
        Checks permission by requesting permission service.
        """
        if not self.internal:
            if not self.permission.is_allowed(self.name, self.user_id, list(payload)):
                raise PermissionDenied(
                    f"You are not allowed to perform action {self.name}."
                )

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        """
        By default this does nothing. Override in subclasses to adjust the updates
        to all instances of the payload. You can only update instances of the model
        of this action.
        If needed, this can also be used to do additional validation on the whole
        payload.
        """
        yield from payload

    def validate_payload_element(self, instance: Dict[str, Any]) -> None:
        """
        Validates one instance of the action payload according to schema class attribute.
        """
        try:
            type(self).schema_validator(instance)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates one instance of the payload. This can be overridden by custom
        action classes.
        """
        return self.update_instance(instance)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates one instance of the payload. This can be overridden by custom
        action classes. Meant to be called inside base_update_instance.
        """
        return instance

    def handle_relation_updates(
        self,
        instance: Dict[str, Any],
    ) -> Iterable[WriteRequestElement]:
        """
        Creates write request elements (with update events) for all relations.
        """
        relation_updates = self.relation_manager.get_relation_updates(
            self.model, instance, self.additional_relation_models
        )
        for fqfield, data in relation_updates.items():
            if data["type"] == "add":
                info_text = f"Object attached to {fqfield.collection}"
            else:
                # data["type"] == "remove"
                info_text = f"Object attachment to {fqfield.collection} reset"
            yield self.build_write_request_element(
                EventType.Update,
                FullQualifiedId(fqfield.collection, fqfield.id),
                info_text,
                {fqfield.field: data["value"]},
            )

    def build_write_request_element(
        self,
        type: EventType,
        fqid: FullQualifiedId,
        information: str,
        fields: Optional[Dict[str, Any]] = None,
    ) -> WriteRequestElement:
        """
        Helper function to create a WriteRequestElement.
        """
        event = Event(
            type=type,
            fqid=fqid,
            fields=fields,
        )
        return WriteRequestElement(
            events=[event],
            information={fqid: [information]},
            user_id=self.user_id,
        )

    def create_write_request_elements(
        self, instance: Dict[str, Any]
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        """
        Creates a write request element for one instance of the current model.
        """
        raise NotImplementedError

    def process_write_request_elements(
        self,
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        # Pre-yield non write request elements, i. e. action response results elements.
        write_request_elements: List[WriteRequestElement] = []
        for item in self.write_request_elements:
            if not isinstance(item, WriteRequestElement):
                yield item
            else:
                write_request_elements.append(item)
        # merge all actual write request elements
        write_request_element = merge_write_request_elements(write_request_elements)
        if write_request_element:
            # sort events: create - update - delete
            events_by_type: Dict[EventType, List[Event]] = defaultdict(list)
            for event in write_request_element.events:
                events_by_type[event["type"]].append(event)
            write_request_element.events = []
            for type in (EventType.Create, EventType.Update, EventType.Delete):
                write_request_element.events.extend(events_by_type[type])

            # Finally yield the merged write request element.
            yield write_request_element

    def validate_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates all model fields according to the model definition.
        """
        for field_name in instance:
            if self.model.has_field(field_name):
                field = self.model.get_field(field_name)
                instance[field_name] = field.validate(instance[field_name])
        return instance

    def validate_relation_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates all relation fields according to the model definition.
        """
        for field in self.model.get_relation_fields():
            if field.equal_fields:
                if field.own_field_name in instance:
                    fields = [field.own_field_name]
                elif isinstance(field, BaseTemplateRelationField):
                    fields = [
                        instance_field
                        for instance_field, replacement in self.get_structured_fields_in_instance(
                            field, instance
                        )
                    ]
                else:
                    continue
                for instance_field in fields:
                    self.check_equal_fields(field, instance, instance_field)
        return instance

    def check_equal_fields(
        self,
        field: BaseRelationField,
        instance: Dict[str, Any],
        instance_field: str,
        additional_equal_fields: List[str] = [],
    ) -> None:
        """
        Asserts that all fields given in field.equal_fields + additional_equal_fields
        are the same in instance and the model referenced by the name instance_field
        of the given field.
        """
        fqids = self.get_field_value_as_fqid_list(field, instance[instance_field])
        equal_fields = field.equal_fields + additional_equal_fields
        for fqid in fqids:
            related_model = self.fetch_model(fqid, equal_fields)
            for equal_field_name in equal_fields:
                if instance.get(equal_field_name) != related_model.get(
                    equal_field_name
                ):
                    raise ActionException(
                        f"The field {equal_field_name} must be equal "
                        f"but differs on {fqid}: "
                        f"{str(instance.get(equal_field_name))} != "
                        f"{str(related_model.get(equal_field_name))}"
                    )

    def get_structured_fields_in_instance(
        self, field: BaseTemplateField, instance: Dict[str, Any]
    ) -> List[Tuple[str, str]]:
        """
        Finds the given field in the given instance and returns the names as well as
        the used replacements of it.
        """
        structured_fields: List[Tuple[str, str]] = []
        for instance_field in instance:
            replacement = field.try_get_replacement(instance_field)
            if replacement:
                structured_fields.append((instance_field, replacement))
        return structured_fields

    def get_field_value_as_fqid_list(
        self, field: BaseRelationField, value: Any
    ) -> List[FullQualifiedId]:
        """ Transforms the given value to an Fqid List. """
        if not isinstance(value, list):
            if value is None:
                value = []
            else:
                value = [value]
        if not isinstance(field, BaseGenericRelationField):
            assert (
                len(field.to) == 1
            )  # non-generic fields can only have one target collection
            value = [FullQualifiedId(field.get_target_collection(), id) for id in value]
        return value

    def fetch_model(
        self, fqid: FullQualifiedId, mapped_fields: List[str] = []
    ) -> Dict[str, Any]:
        """
        Helper method to retrieve an instance from datastore or
        additional_relation_models dictionary.
        """
        if fqid in self.additional_relation_models:
            additional_model = self.additional_relation_models[fqid]
            if mapped_fields:
                return {field: additional_model.get(field) for field in mapped_fields}
            else:
                return additional_model
        else:
            return self.datastore.get(fqid, mapped_fields, lock_result=True)

    def execute_other_action(
        self,
        ActionClass: Type["Action"],
        payload: ActionPayload,
        additional_relation_models: ModelMap = {},
    ) -> None:
        """
        Executes the given action class as a dependent action with the given payload
        and the given addtional relation models. Merges its own additional relation
        models into it.
        The action is fully executed and created WriteRequestElements are appended to
        this action.
        """
        action = ActionClass(
            self.services,
            self.datastore,
            self.relation_manager,
            {**self.additional_relation_models, **additional_relation_models},
        )
        action_results = action.perform(payload, self.user_id)
        for item in action_results:
            # We strip off items of type ActionResponseResultsElement because
            # we do not want such response information in the real action response.
            if isinstance(item, WriteRequestElement):
                self.write_request_elements.append(item)


def merge_write_request_elements(
    write_request_elements: Iterable[WriteRequestElement],
) -> Optional[WriteRequestElement]:
    """
    Merges the given write request elements to one big write request element.
    """
    events: List[Event] = []
    information: Dict[FullQualifiedId, List[str]] = {}
    user_id: Optional[int] = None
    for element in write_request_elements:
        events.extend(element.events)
        for fqid, info_text in element.information.items():
            if information.get(fqid) is None:
                information[fqid] = info_text
            else:
                information[fqid].extend(info_text)
        if user_id is None:
            user_id = element.user_id
        else:
            if user_id != element.user_id:
                raise ValueError(
                    "You can not merge two write request elements of different users."
                )
    if events:
        if user_id is None:
            raise ValueError("At least one of the given user ids must not be None.")
        return WriteRequestElement(
            events=events, information=information, user_id=user_id
        )
    else:
        return None
