import re
from copy import deepcopy
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, Union

import fastjsonschema
from mypy_extensions import TypedDict

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
from ..shared.interfaces.event import Event
from ..shared.interfaces.services import Services
from ..shared.interfaces.write_request_element import WriteRequestElement
from ..shared.patterns import FullQualifiedField, FullQualifiedId
from ..shared.typing import ModelMap
from .action_interface import ActionPayload, ActionResponseResultsElement
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

    services: Services
    permission: PermissionService
    datastore: DatastoreService
    auth: AuthenticationService
    media: MediaService
    user_id: int


class Action(BaseAction, metaclass=SchemaProvider):
    """
    Base class for an action.
    """

    name: str
    model: Model
    schema: Dict
    schema_validator: Callable[[ActionPayload], None]
    internal: bool = False

    def __init__(
        self,
        services: Services,
        additional_relation_models: ModelMap = {},
    ) -> None:
        self.services = services
        self.permission = services.permission()
        self.datastore = services.datastore()
        self.auth = services.authentication()
        self.media = services.media()
        self.additional_relation_models = additional_relation_models

    def perform(
        self, payload: ActionPayload, user_id: int
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.validate(deepcopy(payload))
        self.check_permissions(payload)
        dataset = self.prepare_dataset(payload)
        yield from self.create_write_request_elements(dataset)

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
        Prepares dataset from payload. Also fires all necessary datastore
        queries.
        """
        raise NotImplementedError

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        """
        By default this does nothing. Override in subclasses to adjust the updates
        to all instances of the payload.
        """
        yield from payload

    def validate_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates all model fields according to the model definition.
        """
        for field_name, field in self.model.get_fields():
            if field_name in instance:
                instance[field_name] = field.validate(instance[field_name])
        return instance

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates one instance of the payload. This can be overridden by custom
        action classes.

        This can only be used if payload is a list.

        This is called after initial validation, but before additional relation
        validation.
        """
        return instance

    def validate_relation_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates all relation fields according to the model definition.
        """
        for field_name, field in self.model.get_relation_fields():
            if field.equal_fields:
                if field_name in instance:
                    fields = [field_name]
                elif isinstance(field, BaseTemplateRelationField):
                    fields = [
                        instance_field
                        for instance_field, replacement in self.get_structured_fields_in_instance(
                            field_name, field, instance
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
        self, field_name: str, field: BaseTemplateField, instance: Dict[str, Any]
    ) -> List[Tuple[str, str]]:
        """
        Finds the given field in the given instance and returns the names as well as
        the used replacements of it.
        """
        structured_fields: List[Tuple[str, str]] = []
        for instance_field in instance.keys():
            regex = (
                r"^"
                + field_name[: field.index]
                + r"\$"
                + r"([^_]*)"
                + field_name[field.index :]
                + r"$"
            )
            match = re.match(regex, instance_field)
            if match:
                structured_fields.append((instance_field, match.group(1)))
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
            assert not isinstance(field.to, list)
            value = [FullQualifiedId(field.to, id) for id in value]
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

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        """
        Takes dataset and creates write request elements that can be sent to
        datastore.

        By default it yields self.create_instance_write_request_element and uses
        get_relations_updates() for relations.
        """
        modified_relation_fields: Dict[FullQualifiedField, Any] = {}
        for element in dataset["data"]:
            yield from self.create_instance_write_request_element(element)
            yield from self.get_relations_updates(element, modified_relation_fields)

    def create_instance_write_request_element(
        self, element: Any
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        """
        Creates a write request element for one instance of the current model.
        """
        raise NotImplementedError

    def get_relations_updates(
        self,
        element: Any,
        modified_relation_fields: Dict[FullQualifiedField, Any],
        model: Model = None,
    ) -> Iterable[WriteRequestElement]:
        """
        Creates write request elements (with update events) for all relations.
        """
        if model is None:
            model = self.model
        for fqfield, data in element["relations"].items():
            if fqfield not in modified_relation_fields:
                modified_relation_fields[fqfield] = data["value"]
            else:
                # multiple updates on one fqfield can only happen for list fields
                assert isinstance(modified_relation_fields[fqfield], list)
                if data["type"] == "add":
                    modified_relation_fields[fqfield].append(data["modified_element"])
                else:
                    # data["type"] == "remove"
                    try:
                        modified_relation_fields[fqfield].remove(
                            data["modified_element"]
                        )
                    except ValueError:
                        raise ActionException(
                            f"Can't update relations in {self.name}: {str(data['modified_element'])}"
                            f" is not in {str(modified_relation_fields[fqfield])} (FQField: {fqfield}"
                        )
            if data["type"] == "add":
                info_text = f"Object attached to {model}"
            else:
                # data["type"] == "remove"
                info_text = f"Object attachment to {model} reset"
            event = Event(
                type="update",
                fqid=FullQualifiedId(fqfield.collection, fqfield.id),
                fields={fqfield.field: modified_relation_fields[fqfield]},
            )
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
        relation_fields: Iterable[Tuple[str, BaseRelationField]],
        shortcut: bool = False,
    ) -> Relations:
        """
        Updates relations of the given model for the given fields. Use
        this method in prepare_dataset method.

        If shortcut is True, we assume a create case. That means that all
        relations are added.
        """
        relations: Relations = {}
        for field_name, field in relation_fields:
            handler = RelationsHandler(
                self.datastore,
                model,
                id,
                field,
                field_name,
                obj,
                only_add=shortcut,
                only_remove=False,
                additional_relation_models=self.additional_relation_models,
            )
            result = handler.perform()
            relations.update(result)
        return relations

    def execute_other_action(
        self,
        ActionClass: Type["Action"],
        payload: ActionPayload,
        additional_relation_models: ModelMap = {},
    ) -> Iterable[WriteRequestElement]:
        """
        Executes the given action class as a dependent action with the given payload
        and the given addtional relation models. Merges its own additional relation
        models into it.
        The action is fully executed, so this returns the WriteRequestElements that it
        produces.
        """
        action = ActionClass(
            self.services,
            {**self.additional_relation_models, **additional_relation_models},
        )
        action_results = action.perform(payload, self.user_id)
        for item in action_results:
            # We strip off items of type ActionResponseResultsElement because
            # we do not want such response information in the real action response.
            if isinstance(item, WriteRequestElement):
                yield item


class DummyAction(Action):
    """
    Dummy action that shows, that his action should to be implemented next.
    """

    is_dummy = True

    def perform(
        self, payload: ActionPayload, user_id: int
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
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
    if user_id is None:
        raise ValueError("At least one of the given user ids must not be None.")
    return WriteRequestElement(events=events, information=information, user_id=user_id)
