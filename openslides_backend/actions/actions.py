from typing import Any, Callable, Dict, Iterable, List, Type

import fastjsonschema  # type: ignore
from fastjsonschema import JsonSchemaException  # type: ignore

from .. import logging
from ..shared.exceptions import ActionException, EventStoreException
from ..shared.interfaces import Event
from ..shared.schema import schema_version
from .actions_interface import Payload
from .base import Action

logger = logging.getLogger(__name__)


def prepare_action_map() -> None:
    """
    This function just imports all action modules so that the actions are
    recognized by the system and the register decorator can do its work.

    New modules have to be added here.
    """
    from . import mediafile, topic  # type: ignore # noqa


action_map: Dict[str, Type[Action]] = {}


def register_action(name: str) -> Callable[[Type[Action]], Type[Action]]:
    """
    Decorator to be used for action classes. Registers the class so that it can
    be found by the view.
    """

    def wrapper(action: Type[Action]) -> Type[Action]:
        action_map[name] = action
        return action

    return wrapper


prepare_action_map()


payload_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Schema for actions API",
        "description": "An array of actions.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "action": {
                    "description": "Name of the action to be performed on the server",
                    "type": "string",
                    "minLength": 1,
                },
                "data": {
                    "description": "Data for the action",
                    "type": "array",
                    "items": {"type": "object"},
                    "minItems": 1,
                    "uniqueItems": True,
                },
            },
            "required": ["action", "data"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


class ActionsHandler:
    """
    Actions handler. It is the concret implementation of Actions interface.
    """

    def handle_request(
        self, payload: Payload, user_id: int, services: Dict[str, Any]
    ) -> None:
        """
        Takes payload and user id and handles this request by validating and
        parsing all actions. In the end it sends everything to the event store.
        """
        self.user_id = user_id
        self.services = services  # TODO: Remove it an use DI.

        # Validate payload of request
        try:
            self.validate(payload)
        except JsonSchemaException as exception:
            raise ActionException(exception.message)

        # Parse actions and creates events
        events = self.parse_actions(payload)

        # Send events to database
        try:
            self.services["event_store_adapter"].send(events)
        except EventStoreException as exception:
            raise ActionException(exception.message)

        logger.debug("Request was successful. Send response now.")

    def validate(self, payload: Payload) -> None:
        """
        Validates action requests sent by client. Raises JsonSchemaException if
        input is invalid.
        """
        logger.debug("Validate action request.")
        payload_schema(payload)

    def parse_actions(self, payload: Payload) -> Iterable[Event]:
        """
        Parses action requests send by client. Raises ActionException or
        PermissionDenied if something went wrong.
        """
        all_events: List[Event] = []
        for element in payload:
            logger.debug(f"Action map contains the following actions: {action_map}.")
            action = action_map.get(element["action"])
            if action is None:
                raise ActionException(f"Action {element['action']} does not exist.")
            logger.debug(f"Perform action {element['action']}.")
            events = action(
                self.services["permission_adapter"], self.services["database_adapter"]
            ).perform(element["data"], self.user_id)
            logger.debug(f"Prepared events {events}.")
            all_events.extend(events)
        logger.debug("All events ready.")
        return all_events
