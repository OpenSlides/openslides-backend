from copy import deepcopy
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, TypeVar, cast

import fastjsonschema

from ..shared.env import is_dev_mode
from ..shared.exceptions import (
    ActionException,
    DatastoreLockedException,
    View400Exception,
)
from ..shared.handlers.base_handler import BaseHandler
from ..shared.interfaces.write_request import WriteRequest
from ..shared.schema import schema_version
from . import actions  # noqa
from .relations.relation_manager import RelationManager
from .util.actions_map import actions_map
from .util.typing import (
    ActionError,
    ActionResults,
    ActionsResponse,
    ActionsResponseResults,
    Payload,
    PayloadElement,
)

T = TypeVar("T")

action_data_schema = {
    "$schema": schema_version,
    "title": "Action data",
    "type": "array",
    "items": {"type": "object"},
}

payload_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Schema for action API",
        "description": "An array of actions",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "action": {
                    "description": "Name of the action to be performed on the server",
                    "type": "string",
                    "minLength": 1,
                },
                "data": action_data_schema,
            },
            "required": ["action", "data"],
            "additionalProperties": False,
        },
    }
)


class ActionHandler(BaseHandler):
    """
    Action handler. It is the concrete implementation of Action interface.
    """

    MAX_RETRY = 3

    @classmethod
    def get_health_info(cls) -> Iterable[Tuple[str, Dict[str, Any]]]:
        """
        Returns name and development status of all actions.
        """
        for name in sorted(actions_map):
            action = actions_map[name]
            schema: Dict[str, Any] = deepcopy(action_data_schema)
            schema["items"] = action.schema
            if action.is_singular:
                schema["maxItems"] = 1
            info = dict(
                schema=schema,
            )
            yield name, info

    def handle_request(
        self, payload: Payload, user_id: int, atomic: bool = True
    ) -> ActionsResponse:
        """
        Takes payload and user id and handles this request by validating and
        parsing all actions. In the end it sends everything to the event store.
        """
        self.user_id = user_id

        try:
            payload_schema(payload)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

        results: ActionsResponseResults = []
        if atomic:
            results = self.execute_write_requests(self.parse_actions, payload)
        else:

            def transform_to_list(
                tuple: Tuple[Optional[WriteRequest], ActionResults]
            ) -> Tuple[List[WriteRequest], ActionResults]:
                return ([tuple[0]] if tuple[0] is not None else [], tuple[1])

            for element in payload:
                try:
                    result = self.execute_write_requests(
                        lambda e: transform_to_list(self.perform_action(e)), element
                    )
                    results.append(result)
                except ActionException as exception:
                    error = cast(ActionError, exception.get_json())
                    results.append(error)

        # Return action result
        self.logger.debug("Request was successful. Send response now.")
        return ActionsResponse(
            success=True, message="Actions handled successfully", results=results
        )

    def execute_write_requests(
        self,
        get_write_requests: Callable[..., Tuple[List[WriteRequest], T]],
        *args: Any,
    ) -> T:
        retried = 0
        while True:
            try:
                write_requests, data = get_write_requests(*args)
                if write_requests:
                    self.datastore.write(write_requests)
                return data
            except DatastoreLockedException as exception:
                retried += 1
                if retried > self.MAX_RETRY:
                    raise ActionException(exception.message)

    def parse_actions(
        self, payload: Payload
    ) -> Tuple[List[WriteRequest], ActionsResponseResults]:
        """
        Parses actions request send by client. Raises ActionException or
        PermissionDenied if something went wrong.
        """
        write_requests: List[WriteRequest] = []
        action_response_results: ActionsResponseResults = []
        relation_manager = RelationManager(self.datastore)

        for i, element in enumerate(payload):
            try:
                write_request, results = self.perform_action(element, relation_manager)
            except ActionException as exception:
                exception.action_error_index = i
                raise exception

            if write_request:
                write_requests.append(write_request)
            action_response_results.append(results)

        self.logger.debug("Write request is ready.")
        return (
            write_requests,
            action_response_results,
        )

    def perform_action(
        self,
        action_payload_element: PayloadElement,
        relation_manager: Optional[RelationManager] = None,
    ) -> Tuple[Optional[WriteRequest], ActionResults]:
        action_name = action_payload_element["action"]
        ActionClass = actions_map.get(action_name)
        if ActionClass is None or (ActionClass.internal and not is_dev_mode()):
            raise View400Exception(f"Action {action_name} does not exist.")
        if not relation_manager:
            relation_manager = RelationManager(self.datastore)

        self.logger.debug(f"Perform action {action_name}.")
        action = ActionClass(
            self.services, self.datastore, relation_manager, self.logging
        )
        action_data = deepcopy(action_payload_element["data"])

        try:
            write_request, results = action.perform(action_data, self.user_id)
            if write_request:
                action.validate_required_fields(write_request)
            return (write_request, results)
        except ActionException as exception:
            self.logger.debug(
                f"Error occured on index {action.index}: {exception.message}"
            )
            # -1: error which cannot be directly associated with a single action data
            if action.index > -1:
                exception.action_data_error_index = action.index
            raise exception
