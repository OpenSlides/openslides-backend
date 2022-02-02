from collections import defaultdict
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

import fastjsonschema

from ..models.base import Model, model_registry
from ..models.fields import BaseTemplateField, BaseTemplateRelationField
from ..permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ..permissions.permission_helper import has_organization_management_level, has_perm
from ..permissions.permissions import Permission
from ..services.auth.interface import AuthenticationService
from ..services.datastore.interface import DatastoreService
from ..services.media.interface import MediaService
from ..services.vote.interface import VoteService
from ..shared.exceptions import (
    ActionException,
    AnonymousNotAllowed,
    MissingPermission,
    PermissionDenied,
    RequiredFieldsException,
)
from ..shared.interfaces.event import Event, EventType, ListFields
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services
from ..shared.interfaces.write_request import WriteRequest
from ..shared.patterns import Collection, FullQualifiedId, transform_to_fqids
from .relations.relation_manager import RelationManager, RelationUpdates
from .relations.typing import FieldUpdateElement, ListUpdateElement
from .util.action_type import ActionType
from .util.assert_belongs_to_meeting import assert_belongs_to_meeting
from .util.typing import ActionData, ActionResultElement, ActionResults


class SchemaProvider(type):
    """
    Metaclass to provide pre-compiled JSON schemas for faster validation.
    """

    def __new__(cls, name, bases, attrs):  # type: ignore
        schema = attrs.get("schema")
        if schema is not None:
            attrs["schema_validator"] = fastjsonschema.compile(schema)
        return super().__new__(cls, name, bases, attrs)


def original_instances(method: Callable) -> Callable:
    setattr(method, "_original_instances", True)
    return method


class BaseAction:  # pragma: no cover
    """
    Abstract base class for an action.
    """

    services: Services
    datastore: DatastoreService
    auth: AuthenticationService
    media: MediaService
    vote: VoteService

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
    action_type: ActionType = ActionType.PUBLIC
    permission: Optional[Union[Permission, OrganizationManagementLevel]] = None
    permission_model: Optional[Model] = None
    permission_id: Optional[str] = None
    relation_manager: RelationManager

    write_requests: List[WriteRequest]
    results: ActionResults

    def __init__(
        self,
        services: Services,
        datastore: DatastoreService,
        relation_manager: RelationManager,
        logging: LoggingModule,
        skip_archived_meeting_check: bool = False,
    ) -> None:
        self.services = services
        self.auth = services.authentication()
        self.media = services.media()
        self.vote_service = services.vote()
        self.datastore = datastore
        self.relation_manager = relation_manager
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        if hasattr(self.__class__, "skip_archived_meeting_check"):
            self.skip_archived_meeting_check: bool = (
                self.__class__.skip_archived_meeting_check
            )
        else:
            self.skip_archived_meeting_check = skip_archived_meeting_check
        self.write_requests = []
        self.results = []

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> Tuple[Optional[WriteRequest], Optional[ActionResults]]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.index = 0
        for instance in action_data:
            self.validate_instance(instance)
            self.check_for_archived_meeting(instance)
            # perform permission check not for internal requests or backend_internal actions
            if not internal and self.action_type != ActionType.BACKEND_INTERNAL:
                try:
                    self.check_permissions(instance)
                except MissingPermission as e:
                    msg = f"You are not allowed to perform action {self.name}."
                    e.message = msg + " " + e.message
                    raise e
            self.index += 1
        self.index = -1

        action_data = self.prepare_action_data(action_data)
        instances = self.get_updated_instances(action_data)
        is_original_instances = hasattr(
            self.get_updated_instances, "_original_instances"
        )
        for instance in instances:
            # only increment index if the instances which are iterated here are the
            # same as the ones from the action data list (meaning get_updated_instances was
            # not overridden)
            if is_original_instances:
                self.index += 1

            instance = self.base_update_instance(instance)

            relation_updates = self.handle_relation_updates(instance)
            self.write_requests.extend(relation_updates)

            write_request = self.create_write_requests(instance)
            self.write_requests.extend(write_request)

            if is_original_instances:
                result = self.create_action_result_element(instance)
                self.results.append(result)

        final_write_request = self.process_write_requests()
        # by default, for actions which changed the updated instances, just return None
        if not is_original_instances and not self.results:
            return (final_write_request, None)

        return (final_write_request, self.results)

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        """
        Checks permission by requesting permission service or using internal check.
        """
        # switch between internal and external permission service
        if self.permission:
            if type(self.permission) == OrganizationManagementLevel:
                if has_organization_management_level(
                    self.datastore,
                    self.user_id,
                    cast(OrganizationManagementLevel, self.permission),
                ):
                    return
                raise MissingPermission(self.permission)
            elif type(self.permission) == CommitteeManagementLevel:
                """
                set permission in class to: permission = CommitteeManagementLevel.CAN_MANAGE
                A specialized realisation see in create_update_permissions_mixin.py
                """
                raise NotImplementedError
            else:
                meeting_id = self.get_meeting_id(instance)
                if has_perm(
                    self.datastore,
                    self.user_id,
                    cast(Permission, self.permission),
                    meeting_id,
                ):
                    return
                raise MissingPermission(self.permission)

        msg = f"You are not allowed to perform action {self.name}."
        raise PermissionDenied(msg)

    def check_for_archived_meeting(self, instance: Dict[str, Any]) -> None:
        """Do not allow changing any data in an archived meeting"""
        if self.skip_archived_meeting_check:
            return
        try:
            meeting_id = self.get_meeting_id(instance)
        except AttributeError:
            raise ActionException(
                f"get meeting failed Action: {self.name}. Perhaps you want to use skip_archived_meeting_checks = True attribute"
            )

        fqid = FullQualifiedId(Collection("meeting"), meeting_id)
        meeting = self.datastore.fetch_model(
            fqid,
            ["is_active_in_organization_id", "name"],
        )
        if not meeting.get("is_active_in_organization_id"):
            raise ActionException(
                f'Meeting {meeting.get("name", "")}/{meeting_id} cannot be changed, because it is archived.'
            )

    def assert_not_anonymous(self) -> None:
        """
        Checks if the request user is the Anonymous and raises an error if it is.
        """
        if self.auth.is_anonymous(self.user_id):
            raise AnonymousNotAllowed(self.name)

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        """
        Returns the meeting_id, either directly from the instance or from the datastore.
        Must be overwritten if no meeting_id is present in either!
        """
        if instance.get("meeting_id"):
            return instance["meeting_id"]
        else:
            model = self.model
            if self.permission_model:
                model = self.permission_model
            identifier = "id"
            if self.permission_id:
                identifier = self.permission_id
            db_instance = self.datastore.fetch_model(
                FullQualifiedId(model.collection, instance[identifier]),
                ["meeting_id"],
                exception=True,
            )
            return db_instance["meeting_id"]

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        """
        By default this does nothing. Override in subclasses to adjust the updates
        to all instances of the action data. You can only update instances of the model
        of this action.
        If needed, this can also be used to do additional validation on the whole
        action data.
        """
        yield from action_data

    def prepare_action_data(self, action_data: ActionData) -> ActionData:
        """
        By default this does nothing.
        Override in subclass to pre_get ids.
        """
        return action_data

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        """
        Validates one instance of the action data according to schema class attribute.
        """
        try:
            type(self).schema_validator(instance)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates one instance of the action data. This can be overridden by custom
        action classes.
        """
        return self.update_instance(instance)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates one instance of the action data. This can be overridden by custom
        action classes. Meant to be called inside base_update_instance.
        """
        return instance

    def handle_relation_updates(
        self,
        instance: Dict[str, Any],
    ) -> Iterable[WriteRequest]:
        """
        Creates write request elements (with update events) for all relations.
        """
        relation_updates = self.relation_manager.get_relation_updates(
            self.model, instance, self.name
        )

        return self.handle_relation_updates_helper(relation_updates)

    def handle_relation_updates_helper(
        self,
        relation_updates: RelationUpdates,
    ) -> Iterable[WriteRequest]:
        fields: Optional[Dict[str, Any]]
        for fqfield, data in relation_updates.items():
            list_fields: Optional[ListFields] = None
            if data["type"] in ("add", "remove"):
                data = cast(FieldUpdateElement, data)
                fields = {fqfield.field: data["value"]}
                if data["type"] == "add":
                    info_text = f"Object attached to {fqfield.collection}"
                else:
                    info_text = f"Object attachment to {fqfield.collection} reset"
            elif data["type"] == "list_update":
                data = cast(ListUpdateElement, data)
                info_text = "Object updated"
                fields = None
                list_fields_tmp = {}
                if data["add"]:
                    list_fields_tmp["add"] = {fqfield.field: data["add"]}
                if data["remove"]:
                    list_fields_tmp["remove"] = {fqfield.field: data["remove"]}
                list_fields = cast(ListFields, list_fields_tmp)
            yield self.build_write_request(
                EventType.Update,
                FullQualifiedId(fqfield.collection, fqfield.id),
                info_text,
                fields,
                list_fields,
            )

    def build_write_request(
        self,
        type: EventType,
        fqid: FullQualifiedId,
        information: str,
        fields: Optional[Dict[str, Any]] = None,
        list_fields: Optional[ListFields] = None,
    ) -> WriteRequest:
        """
        Helper function to create a WriteRequest.
        """
        event = Event(
            type=type,
            fqid=fqid,
        )
        if fields:
            event["fields"] = fields
            self.datastore.update_additional_models(fqid, fields)
        if list_fields:
            event["list_fields"] = list_fields
        return WriteRequest(
            events=[event],
            information={fqid: [information]},
            user_id=self.user_id,
            locked_fields={},
        )

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        """
        Creates write requests for one instance of the current model.
        """
        raise NotImplementedError

    def create_action_result_element(
        self, instance: Dict[str, Any]
    ) -> Optional[ActionResultElement]:
        """
        Create an ActionResponseResultsElement describing the result of this action.
        Defaults to None (to be overridden in subclasses).
        """
        return None

    def process_write_requests(
        self,
    ) -> Optional[WriteRequest]:
        """
        Merge all temporarily created write requests to one single write request which
        is returned by this action.
        """
        # merge all actual write requests
        write_request = merge_write_requests(self.write_requests)
        if write_request:
            # sort events: create - update - delete
            events_by_type: Dict[EventType, List[Event]] = defaultdict(list)
            for event in write_request.events:
                events_by_type[event["type"]].append(event)
            write_request.events = []
            for event_type in (EventType.Create, EventType.Update, EventType.Delete):
                write_request.events.extend(events_by_type[event_type])
        return write_request

    def validate_required_fields(self, write_request: WriteRequest) -> None:
        """
        Validate required fields with the events of one WriteRequest.
        Precondition: Events are sorted create/update/delete-events
        Not implemented: required RelationListFields of all types raise a NotImplementedError, if there exist
        one, during getting required_fields from model, except TemplateRelationField and
        TemplateRelationListField with replacement_enum-attribute.
        """
        fdict: Dict[FullQualifiedId, Dict[str, Any]] = {}
        for event in write_request.events:
            if fdict.get(event["fqid"]):
                if event["type"] == EventType.Delete:
                    fdict[event["fqid"]]["type"] = EventType.Delete
                else:
                    fdict[event["fqid"]]["fields"].update(event.get("fields", {}))
            else:
                fdict[event["fqid"]] = {
                    "type": event["type"],
                    "fields": event.get("fields", {}),
                }

        for fqid, v in fdict.items():
            fqid_model: Model = model_registry[fqid.collection]()
            type_ = v["type"]
            instance = v["fields"]
            if type_ in (EventType.Create, EventType.Update):
                is_create = type_ == EventType.Create
                required_fields = [
                    field.own_field_name
                    for field in fqid_model.get_required_fields()
                    if field.check_required_not_fulfilled(instance, is_create)
                ]
                if required_fields:
                    fqid_str = (
                        f"Creation of {fqid}" if is_create else f"Update of {fqid}"
                    )
                    raise RequiredFieldsException(fqid_str, required_fields)

    def validate_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates all model fields according to the model definition.
        """
        try:
            for field_name in instance:
                if self.model.has_field(field_name):
                    field = self.model.get_field(field_name)
                    instance[field_name] = field.validate(instance[field_name])
        except AssertionError as e:
            raise ActionException(str(e))
        return instance

    def validate_relation_fields(self, instance: Dict[str, Any]) -> None:
        """
        Validates all relation fields according to the model definition.
        """
        for field in self.model.get_relation_fields():
            if not field.equal_fields:
                continue

            if field.own_field_name in instance:
                fields = [field.own_field_name]
            elif isinstance(field, BaseTemplateRelationField):
                fields = [
                    instance_field
                    for instance_field, replacement in self.get_structured_fields_in_instance(
                        field, instance
                    )
                ]
                if not fields:
                    continue
            else:
                continue

            for equal_field in field.equal_fields:
                if not (own_equal_field_value := instance.get(equal_field)):
                    fqid = FullQualifiedId(self.model.collection, instance["id"])
                    db_instance = self.datastore.fetch_model(
                        fqid,
                        [equal_field],
                    )
                    if not (own_equal_field_value := db_instance.get(equal_field)):
                        raise ActionException(
                            f"{fqid} has no value for the field {equal_field}"
                        )
                for instance_field in fields:
                    fqids = transform_to_fqids(
                        instance[instance_field], field.get_target_collection()
                    )
                    if equal_field == "meeting_id":
                        assert_belongs_to_meeting(
                            self.datastore, fqids, own_equal_field_value
                        )
                    else:
                        for fqid in fqids:
                            related_instance = self.datastore.fetch_model(
                                fqid,
                                [equal_field],
                            )
                            if (
                                related_instance.get(equal_field)
                                != own_equal_field_value
                            ):
                                raise ActionException(
                                    f"The relation {field.own_field_name} requires the following "
                                    f"fields to be equal:\n"
                                    f"{field.own_collection}/{instance['id']}/{equal_field}: "
                                    f"{own_equal_field_value}\n"
                                    f"{fqid}/{equal_field}: "
                                    f"{related_instance.get(equal_field)}"
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

    def apply_instance(
        self, instance: Dict[str, Any], fqid: Optional[FullQualifiedId] = None
    ) -> None:
        if not fqid:
            fqid = FullQualifiedId(self.model.collection, instance["id"])
        self.datastore.update_additional_models(fqid, instance)

    def execute_other_action(
        self,
        ActionClass: Type["Action"],
        action_data: ActionData,
        skip_archived_meeting_check: bool = False,
    ) -> Optional[ActionResults]:
        """
        Executes the given action class as a dependent action with the given action
        data and the given addtional relation models. Merges its own additional
        relation models into it.
        The action is fully executed and created WriteRequests are appended to
        this action.
        The attribute skip_archived_meeting_check" from the calling class is inherited
        to the called class if set. Usually this is needed for cascading deletes from
        outside of meeting.
        """
        if hasattr(self.__class__, "skip_archived_meeting_check"):
            skip_archived_meeting_check = self.__class__.skip_archived_meeting_check

        action = ActionClass(
            self.services,
            self.datastore,
            self.relation_manager,
            self.logging,
            skip_archived_meeting_check,
        )
        write_request, action_results = action.perform(
            action_data, self.user_id, internal=True
        )
        if write_request:
            self.write_requests.append(write_request)
        return action_results

    def get_on_success(self, action_data: ActionData) -> Callable[[], None]:
        """
        Can be overridden by actions to return a cleanup method to execute
        after the result was successfully written to the DS.
        """


def merge_write_requests(
    write_requests: Iterable[WriteRequest],
) -> Optional[WriteRequest]:
    """
    Merges the given write request elements to one big write request element.
    """
    events: List[Event] = []
    information: Dict[FullQualifiedId, List[str]] = {}
    user_id: Optional[int] = None
    for element in write_requests:
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
        return WriteRequest(
            events=events, information=information, user_id=user_id, locked_fields={}
        )
    else:
        return None
