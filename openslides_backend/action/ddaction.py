from collections import defaultdict
from collections.abc import Callable
from abc import abstractmethod
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, cast

import fastjsonschema
from psycopg import sql
from psycopg.types.json import Jsonb

from openslides_backend.shared.base_service_provider import BaseServiceProvider

from ..models.base import Model, model_registry
from ..services.database.commands import GetManyRequest
from ..services.database.extended_database import ExtendedDatabase
from ..services.database.interface import Database
from ..shared.exceptions import ActionException, BadCodingException, MissingPermission, PermissionDenied
from ..shared.interfaces.env import Env
from ..shared.interfaces.event import Event
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services
from ..shared.interfaces.write_request import WriteRequest
from ..shared.otel import make_span
from ..shared.patterns import (
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from ..shared.typing import HistoryInformation
from .action import Action, SchemaProvider
from .relations.relation_manager import RelationManager
from .util.action_type import ActionType
from .util.typing import ActionData, ActionResults
from ..permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ..permissions.permission_helper import has_organization_management_level, has_perm
from ..permissions.permissions import Permission


class DDAction(BaseServiceProvider, metaclass=SchemaProvider):
    """
    Base class for a database-direct action.
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
    # history_information: str | None = None
    # history_relation_field: str | None = None
    # add_self_history_information: bool = False
    # own_history_information_first: bool = False

    # relation_manager: RelationManager

    action_data: ActionData
    instances: list[dict[str, Any]]
    events: list[Event]
    results: ActionResults
    # cascaded_actions_history: HistoryInformation
    internal: bool

    def __init__(
        self,
        services: Services,
        database: Database,
        relation_manager: RelationManager,
        logging: LoggingModule,
        env: Env,
        skip_archived_meeting_check: bool | None = None,
        use_meeting_ids_for_archived_meeting_check: bool | None = None,
    ) -> None:
        super().__init__(services, database, logging)
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
        # self.cascaded_actions_history = {}

    def perform(
        self,
        action_data: ActionData,
        user_id: int,
        internal: bool = False,
        is_sub_call: bool = False,
        history_position_id: int | None = None,
    ) -> ActionResults | None:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.index = 0
        self.internal = internal
        self.is_sub_call = is_sub_call
        self.history_position_id = history_position_id

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

        self.action_data = deepcopy(action_data)
        return self.write_instances(self.action_data)

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

    @abstractmethod
    def write_instances(self, action_data: ActionData) -> ActionResults | None:
        """
        Method that calculates all necessary changes for the entire action data and writes it all.
        To be overwritten by subclasses.
        """
        ...

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

    def get_meeting_id(self, instance: dict[str, Any]) -> int:
        """
        Returns the meeting_id, either directly from the instance or from the datastore.
        Must be overwritten if no meeting_id is present in either!
        """
        if instance.get("meeting_id"):
            return instance["meeting_id"]
        else:
            model = self.model
            # if self.permission_model:
            #     model = self.permission_model
            identifier = "id"
            # if self.permission_id:
            #     identifier = self.permission_id
            db_instance = self.datastore.get(
                fqid_from_collection_and_id(model.collection, instance[identifier]),
                ["meeting_id"],
                lock_result=False,
            )
            return db_instance["meeting_id"]

    def validate_instance(self, instance: dict[str, Any]) -> None:
        """
        Validates one instance of the action data according to schema class attribute.
        """
        try:
            type(self).schema_validator(
                {
                    # fmt: off
                    field:
                        int(value.timestamp()) if isinstance(value, datetime)
                        else int(value.total_seconds()) if isinstance(value, timedelta)
                        else str(value) if isinstance(value, Decimal)
                        else value.obj if isinstance(value, Jsonb)
                        else value
                    for field, value in instance.items()
                    # fmt: on
                }
            )
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(f"Action {self.name}: " + exception.message)

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

    def execute_other_action(
        self,
        ActionClass: type[Action] | type["DDAction"],
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
            if isinstance(action, Action):
                # Code for if the sub-action is old-style.
                # TODO: To be deleted along with the old-style actions
                return self._execute_old_style_action(action, action_data, skip_history)
            else:
                results = action.perform(
                    action_data, self.user_id, internal=True, is_sub_call=True
                )
                if hpi := action.history_position_id:
                    self.history_position_id = hpi
                return results

    def write_history_information(
        self, history_information: HistoryInformation
    ) -> None:
        create_history = history_information
        update_history: dict[int, list[str]] = {}
        if self.history_position_id is None:
            # TODO: Create a history_position
            self.history_position_id = self.datastore.insert_model(
                "history_position",
                {
                    "original_user_id": self.user_id,
                    "user_id": self.user_id,
                    "timestamp": datetime.now(),
                },
            )[1]["id"]
        else:
            found = self.datastore.execute_custom_select(
                sql.SQL(
                    "id, model_id, entries FROM history_entry_t WHERE position_id = {position_id} AND model_id IN {fqids}"
                ).format(
                    fqids=tuple(history_information),
                    position_id=self.history_position_id,
                )
            )
            for model in found:
                update_history[model["id"]] = [
                    *model.get("entries", []),
                    *history_information[fqid := model["model_id"]],
                ]
                del create_history[fqid]
        if create_history:
            collection_to_ids: dict[str, list[int]] = defaultdict(list)
            for fqid in history_information:
                collection_to_ids[collection_from_fqid(fqid)].append(id_from_fqid(fqid))
            data = self.datastore.get_many(
                [
                    GetManyRequest(collection, ids, ["meeting_id"])
                    for collection, ids in collection_to_ids.items()
                    if model_registry[collection]().try_get_field("meeting_id")
                ],
                use_changed_models=False,
            )
            for fqid, entries in create_history.items():
                self.datastore.insert_model(
                    "history_entry",
                    {
                        "entries": entries,
                        "original_model_id": fqid,
                        "model_id": fqid,
                        "position_id": self.history_position_id,
                        "meeting_id": data.get(collection_from_fqid(fqid), {})
                        .get(id_from_fqid(fqid), {})
                        .get("meeting_id"),
                    },
                )
        if update_history:
            for id_, entries in update_history.items():
                self.datastore.update_model("history_entry", id_, {"entries": entries})

    # ----------------------------------------------------------------------------------------------------
    # CODE FOR COMPATIBILITY WITH OLD_STYLE ACTIONS.
    # TO BE DELETED WHEN THOSE ARE REMOVED COMPLETELY.

    def _execute_old_style_action(
        self, action: Action, action_data: ActionData, skip_history: bool
    ) -> ActionResults | None:
        cast(ExtendedDatabase, self.datastore).toggle_changed_models(True)
        write_request, action_results = action.perform(
            action_data, self.user_id, internal=True, is_sub_call=True
        )
        if write_request:
            if events := write_request.events:
                self.datastore.write(WriteRequest(events=events))
            if not skip_history and (history_information := write_request.information):
                self.write_history_information(history_information)
        cast(ExtendedDatabase, self.datastore).toggle_changed_models(False)
        return action_results
