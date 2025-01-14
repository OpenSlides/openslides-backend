from collections import defaultdict
from collections.abc import Callable, Iterable
from copy import deepcopy
from typing import Any, TypeVar, cast

import fastjsonschema

from openslides_backend.shared.base_service_provider import BaseServiceProvider

from ..models.base import Model, model_registry
from ..models.fields import BaseRelationField
from ..permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ..permissions.permission_helper import has_organization_management_level, has_perm
from ..permissions.permissions import Permission
from ..presenter.base import BasePresenter
from ..services.database.commands import GetManyRequest
from ..services.database.interface import Database
from ..shared.exceptions import (
    ActionException,
    AnonymousNotAllowed,
    MissingPermission,
    PermissionDenied,
    RequiredFieldsException,
)
from ..shared.interfaces.env import Env
from ..shared.interfaces.event import Event, EventType, ListFields
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services
from ..shared.interfaces.write_request import WriteRequest
from ..shared.otel import make_span
from ..shared.patterns import (
    FullQualifiedId,
    collection_from_fqid,
    fqid_and_field_from_fqfield,
    fqid_from_collection_and_id,
    transform_to_fqids,
)
from ..shared.typing import DeletedModel, HistoryInformation
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


ORIGINAL_INSTANCES_FLAG = "_original_instances"


def original_instances(method: Callable) -> Callable:
    """
    Marker decorator for get_updated_instances to indicate that the method returns the original
    instances from the action data in the same order. Must be set to create action result.
    """
    setattr(method, ORIGINAL_INSTANCES_FLAG, True)
    return method


T = TypeVar("T", bound=WriteRequest)


class Action(BaseServiceProvider, metaclass=SchemaProvider):
    """
    Base class for an action.
    """

    name: str
    model: Model
    schema: dict
    schema_validator: Callable[[dict[str, Any]], None]

    is_singular: bool = False
    action_type: ActionType = ActionType.PUBLIC
    permission: Permission | OrganizationManagementLevel | None = None
    permission_model: Model | None = None
    permission_id: str | None = None
    skip_archived_meeting_check: bool = False
    use_meeting_ids_for_archived_meeting_check: bool = False
    history_information: str | None = None
    history_relation_field: str | None = None
    add_self_history_information: bool = False
    own_history_information_first: bool = False

    relation_manager: RelationManager

    action_data: ActionData
    instances: list[dict[str, Any]]
    events: list[Event]
    results: ActionResults
    cascaded_actions_history: HistoryInformation
    internal: bool

    def __init__(
        self,
        services: Services,
        datastore: Database,
        relation_manager: RelationManager,
        logging: LoggingModule,
        env: Env,
        skip_archived_meeting_check: bool | None = None,
        use_meeting_ids_for_archived_meeting_check: bool | None = None,
    ) -> None:
        super().__init__(services, datastore, logging)
        self.relation_manager = relation_manager
        self.logger = logging.getLogger(__name__)
        self.env = env
        if skip_archived_meeting_check is not None:
            self.skip_archived_meeting_check = skip_archived_meeting_check
        if use_meeting_ids_for_archived_meeting_check is not None:
            self.use_meeting_ids_for_archived_meeting_check = (
                use_meeting_ids_for_archived_meeting_check
            )
        self.events = []
        self.results = []
        self.cascaded_actions_history = {}

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> tuple[WriteRequest | None, ActionResults | None]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.index = 0
        self.internal = internal

        # prefetch as much data as possible
        self.prefetch(action_data)

        for i, instance in enumerate(action_data):
            self.validate_instance(instance)
            cast(list[dict[str, Any]], action_data)[i] = self.validate_fields(instance)
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
        self.action_data = deepcopy(action_data)
        self.instances = list(self.get_updated_instances(action_data))
        is_original_instances = hasattr(
            self.get_updated_instances, ORIGINAL_INSTANCES_FLAG
        )
        for instance in self.instances:
            # only increment index if the instances which are iterated here are the
            # same as the ones from the action data list (meaning get_updated_instances was
            # not overridden)
            if is_original_instances:
                self.index += 1

            instance = self.base_update_instance(instance)

            relation_updates = self.handle_relation_updates(instance)
            self.events.extend(relation_updates)

            events = self.create_events(instance)
            self.events.extend(events)

            if is_original_instances:
                result = self.create_action_result_element(instance)
                self.results.append(result)

        write_request = self.build_write_request()
        # by default, for actions which changed the updated instances, just return None
        if not is_original_instances and not self.results:
            return (write_request, None)

        return (write_request, self.results)

    def prefetch(self, action_data: ActionData) -> None:
        """
        Implement in subclasses to prefetch data for the action.
        """

    def check_permissions(self, instance: dict[str, Any]) -> None:
        """
        Checks permission by requesting permission service or using internal check.
        """
        if self.permission:
            if isinstance(self.permission, OrganizationManagementLevel):
                if has_organization_management_level(
                    self.datastore,
                    self.user_id,
                    cast(OrganizationManagementLevel, self.permission),
                ):
                    return
                raise MissingPermission(self.permission)
            elif isinstance(self.permission, CommitteeManagementLevel):
                """
                set permission in class to: permission = CommitteeManagementLevel.CAN_MANAGE
                A specialized realisation see in create_update_permissions_mixin.py
                """
                raise NotImplementedError()
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

    def check_for_archived_meeting(self, instance: dict[str, Any]) -> None:
        """Do not allow changing any data in an archived meeting"""
        if self.skip_archived_meeting_check:
            return
        try:
            if self.use_meeting_ids_for_archived_meeting_check:
                meeting_ids = instance["meeting_ids"]
            else:
                meeting_ids = [self.get_meeting_id(instance)]
        except AttributeError:
            raise ActionException(
                f"get meeting failed Action: {self.name}. Perhaps you want to use skip_archived_meeting_checks = True attribute"
            )
        gmr = GetManyRequest(
            "meeting", meeting_ids, ["id", "is_active_in_organization_id", "name"]
        )
        gm_result = self.datastore.get_many([gmr], lock_result=False)
        for meeting in gm_result.get("meeting", {}).values():
            if not meeting.get("is_active_in_organization_id"):
                raise ActionException(
                    f'Meeting {meeting.get("name", "")}/{meeting["id"]} cannot be changed, because it is archived.'
                )

    def assert_not_anonymous(self) -> None:
        """
        Checks if the request user is the Anonymous and raises an error if it is.
        """
        if self.auth.is_anonymous(self.user_id):
            raise AnonymousNotAllowed(self.name)

    def get_meeting_id(self, instance: dict[str, Any]) -> int:
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
            db_instance = self.datastore.get(
                fqid_from_collection_and_id(model.collection, instance[identifier]),
                ["meeting_id"],
                lock_result=False,
            )
            return db_instance["meeting_id"]

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        """
        By default this does nothing. Override in subclasses to adjust the updates
        to all instances of the action data. You can only update instances of the model
        of this action. If overridden and not decorated with @original_instances, no
        action results will be created.
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

    def validate_instance(self, instance: dict[str, Any]) -> None:
        """
        Validates one instance of the action data according to schema class attribute.
        """
        try:
            type(self).schema_validator(instance)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Updates one instance of the action data. This can be overridden by custom
        action classes.
        """
        return self.update_instance(instance)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Updates one instance of the action data. This can be overridden by custom
        action classes. Meant to be called inside base_update_instance.
        """
        return instance

    def handle_relation_updates(
        self,
        instance: dict[str, Any],
    ) -> Iterable[Event]:
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
    ) -> Iterable[Event]:
        for fqfield, data in relation_updates.items():
            fields: dict[str, Any] = {}
            list_fields: ListFields = {}
            fqid, field = fqid_and_field_from_fqfield(fqfield)
            if data["type"] in ("add", "remove"):
                data = cast(FieldUpdateElement, data)
                fields[field] = data["value"]
            elif data["type"] == "list_update":
                data = cast(ListUpdateElement, data)
                if data["add"]:
                    list_fields["add"] = {field: data["add"]}
                if data["remove"]:
                    list_fields["remove"] = {field: data["remove"]}
            yield self.build_event(
                EventType.Update,
                fqid,
                fields,
                list_fields,
            )

    def build_event(
        self,
        type: EventType,
        fqid: FullQualifiedId,
        fields: dict[str, Any] | None = None,
        list_fields: ListFields | None = None,
    ) -> Event:
        """
        Helper function to create a WriteRequest.
        """
        event = Event(
            type=type,
            fqid=fqid,
        )
        if fields:
            event["fields"] = fields
            self.datastore.apply_changed_model(fqid, fields)
        if list_fields:
            event["list_fields"] = list_fields
        return event

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        """
        Creates events for one instance of the current model. To be overriden in subclasses.
        """
        raise NotImplementedError()

    def create_action_result_element(
        self, instance: dict[str, Any]
    ) -> ActionResultElement | None:
        """
        Create an ActionResponseResultsElement describing the result of this action.
        Defaults to None (to be overridden in subclasses).
        """
        return None

    def build_write_request(
        self,
    ) -> WriteRequest | None:
        """
        Merge all created events to one single write request which is returned by this action.
        """
        return self._build_write_request(WriteRequest([]))

    def _build_write_request(
        self,
        write_request: T,
    ) -> T | None:
        # merge all events, if any, into a write request
        if self.events:
            # sort events: create - update - delete
            events_by_type: dict[EventType, list[Event]] = defaultdict(list)
            for event in self.events:
                self.apply_event(event)
                events_by_type[event["type"]].append(event)
            write_request.information = self.get_full_history_information()
            write_request.user_id = self.user_id
            write_request.events.extend(events_by_type[EventType.Create])
            write_request.events.extend(
                self.merge_update_events(events_by_type[EventType.Update])
            )
            write_request.events.extend(events_by_type[EventType.Delete])
            return write_request
        return None

    def get_full_history_information(self) -> HistoryInformation | None:
        """
        Get history information for this action and all cascading ones. Should only be overridden if
        the order should be changed.
        """
        information = self.get_history_information()
        if self.cascaded_actions_history or information:
            if self.own_history_information_first:
                return merge_history_informations(
                    information, self.cascaded_actions_history
                )
            else:
                return merge_history_informations(
                    self.cascaded_actions_history, information
                )
        else:
            return None

    def get_history_information(self) -> HistoryInformation | None:
        """
        Get the history information for this action. Can be overridden to get
        context-dependent information.
        """
        if self.history_information is None:
            return None

        information = {}
        instances = (
            self.get_instances_with_fields(["id", self.history_relation_field])
            if self.history_relation_field
            else self.instances
        )
        for instance in instances:
            fqids = []
            if self.history_relation_field:
                field = self.model.get_field(self.history_relation_field)
                assert isinstance(field, BaseRelationField)
                fqids = transform_to_fqids(
                    instance[self.history_relation_field], field.get_target_collection()
                )
            if not self.history_relation_field or self.add_self_history_information:
                fqids.append(
                    fqid_from_collection_and_id(self.model.collection, instance["id"])
                )
            for fqid in fqids:
                information[fqid] = [self.history_information]
        return information

    def get_instances_with_fields(
        self, fields: list[str], instances: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        if not instances:
            instances = self.instances
        # if any field is missing in any instance, we need to access the datastore
        if any(not instance.get(field) for field in fields for instance in instances):
            result = self.datastore.get_many(
                [
                    GetManyRequest(
                        self.model.collection,
                        [instance["id"] for instance in instances],
                        fields,
                    )
                ],
                lock_result=False,
                use_changed_models=False,
            )
            return list(result.get(self.model.collection, {}).values())
        else:
            return instances

    def get_field_from_instance(self, field: str, instance: dict[str, Any]) -> Any:
        instances = self.get_instances_with_fields([field], [instance])
        return instances[0].get(field) if instances else None

    def merge_update_events(self, update_events: list[Event]) -> list[Event]:
        """
        This is optimation to reduce the amount of update events.
        """
        events_by_fqid = defaultdict(list)
        for event in update_events:
            events_by_fqid[event["fqid"]].append(event)

        result: list[Event] = []
        for fqid in events_by_fqid:
            result.extend(self.merge_update_events_for_fqid(events_by_fqid[fqid]))

        return result

    def merge_update_events_for_fqid(self, events: list[Event]) -> list[Event]:
        result: list[Event] = []
        trailing_index: int | None = None
        count = 0
        for event in events[::-1]:
            if not event.get("list_fields"):
                if trailing_index is None:
                    trailing_index = count + 1
                    result.insert(0, event)
                else:
                    new_fields_dict = event.get("fields") or {}
                    new_fields_dict.update(result[-trailing_index]["fields"] or {})
                    result[-trailing_index]["fields"] = new_fields_dict
            else:
                count += 1
                result.insert(0, event)

        return result

    def apply_event(self, event: Event) -> None:
        """
        Applies the given event to the changed_models in the datastore.
        """
        if event["type"] in (EventType.Create, EventType.Update):
            if fields := event.get("fields"):
                self.datastore.apply_changed_model(event["fqid"], fields)
        elif event["type"] == EventType.Delete:
            self.datastore.apply_changed_model(event["fqid"], DeletedModel())

    def validate_write_request(self, write_request: WriteRequest) -> None:
        """
        Validate required fields with the events of one WriteRequest.
        Precondition: Events are sorted create/update/delete-events
        Not implemented: required RelationListFields of all types raise a NotImplementedError, if there exist
        one, during getting required_fields from model.
        Also check for fields in the write request, which are not model fields.
        """
        fdict: dict[FullQualifiedId, dict[str, Any]] = {}
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
            fqid_model: Model = model_registry[collection_from_fqid(fqid)]()
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

            # check all fields in the write request
            for field_name, value in instance.items():
                if fqid_model.has_field(field_name):
                    fqid_model.get_field(field_name).validate_with_schema(
                        fqid, field_name, value
                    )
                else:
                    raise ActionException(
                        f"{field_name} is not a valid field for model {fqid_model.collection}."
                    )

    def validate_fields(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Validates and sanitizes all model fields according to the model definition.
        """
        try:
            for field_name in instance:
                if self.model.has_field(field_name):
                    field = self.model.get_field(field_name)
                    instance[field_name] = field.validate(instance[field_name])
        except AssertionError as e:
            raise ActionException(str(e))
        except ValueError as e:
            raise ActionException(str(e))
        return instance

    def validate_relation_fields(self, instance: dict[str, Any]) -> None:
        """
        Validates all relation fields according to the model definition.
        """
        for field in self.model.get_relation_fields():
            if not field.equal_fields or field.own_field_name not in instance:
                continue

            fields = [field.own_field_name]
            for equal_field in field.equal_fields:
                if not (own_equal_field_value := instance.get(equal_field)):
                    fqid = fqid_from_collection_and_id(
                        self.model.collection, instance["id"]
                    )
                    db_instance = self.datastore.get(
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
                            related_instance = self.datastore.get(
                                fqid,
                                [equal_field],
                            )
                            if str(related_instance.get(equal_field)) != str(
                                own_equal_field_value
                            ):
                                raise ActionException(
                                    f"The relation {field.own_field_name} requires the following "
                                    f"fields to be equal:\n"
                                    f"{field.own_collection}/{instance['id']}/{equal_field}: "
                                    f"{own_equal_field_value}\n"
                                    f"{fqid}/{equal_field}: "
                                    f"{related_instance.get(equal_field)}"
                                )

    def apply_instance(
        self, instance: dict[str, Any], fqid: FullQualifiedId | None = None
    ) -> None:
        if not fqid:
            fqid = fqid_from_collection_and_id(self.model.collection, instance["id"])
        self.datastore.apply_changed_model(fqid, instance)

    def execute_other_action(
        self,
        ActionClass: type["Action"],
        action_data: ActionData,
        skip_archived_meeting_check: bool = False,
        skip_history: bool = False,
    ) -> ActionResults | None:
        """
        Executes the given action class as a dependent action with the given action
        data and the given addtional relation models. Merges its own additional
        relation models into it.
        The action is fully executed and created WriteRequests are appended to
        this action.
        The attribute skip_archived_meeting_check from the calling class is inherited
        to the called class if set. Usually this is needed for cascading deletes from
        outside of meeting.
        """
        with make_span(self.env, f"other action {ActionClass}"):
            if self.skip_archived_meeting_check:
                skip_archived_meeting_check = self.skip_archived_meeting_check

            action = ActionClass(
                self.services,
                self.datastore,
                self.relation_manager,
                self.logging,
                self.env,
                skip_archived_meeting_check,
            )
            write_request, action_results = action.perform(
                action_data, self.user_id, internal=True
            )
            if write_request:
                self.events.extend(write_request.events)
                if not skip_history and write_request.information:
                    merge_history_informations(
                        self.cascaded_actions_history, write_request.information
                    )
            return action_results

    def get_on_success(self, action_data: ActionData) -> Callable[[], None] | None:
        """
        Can be overridden by actions to return a cleanup method to execute
        after the result was successfully written to the DS.
        """
        return None

    def get_on_failure(self, action_data: ActionData) -> Callable[[], None] | None:
        """
        Can be overridden by actions to return a cleanup method to execute
        after an error appeared in an action.
        """
        return None

    def execute_presenter(
        self, PresenterClass: type[BasePresenter], payload: Any
    ) -> Any:
        presenter_instance = PresenterClass(
            payload,
            self.services,
            self.datastore,
            self.logging,
            self.user_id,
        )
        presenter_instance.validate()
        return presenter_instance.get_result()


def merge_history_informations(
    a: HistoryInformation | None, *other: HistoryInformation | None
) -> HistoryInformation:
    """
    Merges multiple history informations. All latter ones are merged into the first one.
    """
    if a is None:
        a = {}
    for b in other:
        if b is None:
            b = {}
        for fqid, information in b.items():
            if fqid in a:
                a[fqid].extend(information)
            else:
                a[fqid] = information
    return a
