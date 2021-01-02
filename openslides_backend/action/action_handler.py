from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Tuple

import fastjsonschema

from ..shared.exceptions import ActionException, DatastoreException, EventStoreException
from ..shared.handlers.base_handler import BaseHandler
from ..shared.interfaces.write_request_element import WriteRequestElement
from ..shared.schema import schema_version
from . import actions  # noqa
from .action import merge_write_request_elements
from .relations.relation_manager import RelationManager
from .util.actions_map import actions_map
from .util.typing import (
    ActionResponse,
    ActionResponseResults,
    ActionResponseResultsElement,
    Payload,
)

action_payload_schema = {
    "$schema": schema_version,
    "title": "Action payload",
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
                "data": action_payload_schema,
            },
            "required": ["action", "data"],
            "additionalProperties": False,
        },
    }
)


class ActionHandler(BaseHandler):
    """
    Action handler. It is the concret implementation of Action interface.
    """

    MAX_RETRY = 3

    @classmethod
    def get_health_info(cls) -> Iterable[Tuple[str, Dict[str, Any]]]:
        """
        Returns name and development status of all actions.
        """
        for name in sorted(actions_map):
            action = actions_map[name]
            if getattr(action, "is_dummy", False):
                yield name, dict(status="Not implemented")
            else:
                schema: Dict[str, Any] = deepcopy(action_payload_schema)
                schema["items"] = action.schema
                if action.is_singular:
                    schema["maxItems"] = 1
                info = dict(
                    schema=schema,
                    permission=action.get_permission_description(),
                )
                yield name, info

    def handle_request(self, payload: Payload, user_id: int) -> ActionResponse:
        """
        Takes payload and user id and handles this request by validating and
        parsing all actions. In the end it sends everything to the event store.
        """
        self.user_id = user_id

        # Validate payload of request
        try:
            self.validate(payload)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)

        retried = 0
        payload_copy = deepcopy(payload)
        while True:
            # Parse actions and creates events
            write_request_element, results = self.parse_actions(payload)

            # Send events to datastore
            if write_request_element:
                try:
                    self.datastore.write(write_request_element)
                except DatastoreException as exception:
                    retried += 1
                    payload = deepcopy(payload_copy)
                    if retried > self.MAX_RETRY:
                        raise ActionException(exception.message)
                    continue
                except EventStoreException as exception:
                    raise ActionException(exception.message)
            break
        # Return action result
        # TODO: This is a fake result because in this place all actions were
        # always successful.
        self.logger.debug("Request was successful. Send response now.")
        return ActionResponse(
            success=True, message="Actions handled successfully", results=results
        )

    def validate(self, payload: Payload) -> None:
        """
        Validates actions requests sent by client. Raises JsonSchemaException if
        input is invalid.
        """
        self.logger.debug("Validate actions request.")
        payload_schema(payload)

    def parse_actions(
        self, payload: Payload
    ) -> Tuple[Optional[WriteRequestElement], ActionResponseResults]:
        """
        Parses actions request send by client. Raises ActionException or
        PermissionDenied if something went wrong.
        """
        all_write_request_elements: List[WriteRequestElement] = []
        all_action_response_results: ActionResponseResults = []
        relation_manager = RelationManager(self.datastore)

        for element in payload:
            action_name = element["action"]
            ActionClass = actions_map.get(action_name)
            if ActionClass is None or ActionClass.internal:
                raise ActionException(f"Action {action_name} does not exist.")

            self.logger.debug(f"Perform action {action_name}.")
            action = ActionClass(self.services, self.datastore, relation_manager)
            action_results = action.perform(element["data"], self.user_id)

            response_elements: List[Optional[ActionResponseResultsElement]] = []
            for item in action_results:
                if isinstance(item, WriteRequestElement):
                    self.logger.debug(f"Prepared write request element {item}.")
                    all_write_request_elements.append(item)
                else:
                    # item = cast(ActionResponseResultsElement, item)
                    self.logger.debug(f"Got action response element {item}.")
                    response_elements.append(item)
            all_action_response_results.append(response_elements or None)

        self.logger.debug("Write request is ready.")
        return (
            merge_write_request_elements(all_write_request_elements),
            all_action_response_results,
        )
