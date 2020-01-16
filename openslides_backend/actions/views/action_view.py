from typing import Dict, Iterable, List

from fastjsonschema import JsonSchemaException  # type: ignore

from .. import logging
from ..actions.action_map import action_map
from ..actions.base import ActionException, PermissionDenied
from ..adapters.authentication import AuthenticationException
from ..adapters.event_store import EventStoreException
from ..adapters.protocols import Event
from ..general.exception import BackendBaseException
from .base import View
from .protocols import CustomException, Request
from .schema import action_view_schema
from .view_map import register_view

logger = logging.getLogger(__name__)


class ViewsException(BackendBaseException):
    pass


@register_view("ActionView")
class ActionView(View):
    def dispatch(self, request: Request, **kwargs: dict) -> None:
        """
        Dispatches request to the viewpoint.
        """
        logger.debug("Start dispatching request.")

        # Get request user id
        try:
            self.user_id = self.authentication_adapter.get_user(request.headers)
        except AuthenticationException as exception:
            self.handle_error(exception, 400)

        # Validate payload of request
        if not request.is_json:
            self.handle_error(
                ViewsException(
                    "Wrong media type. Use 'Content-Type: application/json' instead."
                ),
                400,
            )
        action_requests = request.json
        try:
            self.validate(action_requests)
        except JsonSchemaException as exception:
            self.handle_error(exception, 400)

        # Parse actions and creates events
        try:
            events = self.parse_actions(action_requests)
        except PermissionDenied as exception:
            self.handle_error(exception, 403)
        except ActionException as exception:
            self.handle_error(exception, 400)

        # Send events to database
        try:
            self.event_store_adapter.send(events)
        except EventStoreException as exception:
            self.handle_error(exception, 400)

        logger.debug("Request was successful. Send response now.")

    def validate(self, action_requests: List[Dict]) -> None:
        """
        Validates action requests sent by client. Raises JsonSchemaException if
        input is invalid.
        """
        logger.debug("Validate action request.")
        action_view_schema(action_requests)

    def parse_actions(self, action_requests: List[Dict]) -> Iterable[Event]:
        """
        Parses action requests send by client. Raises ActionException if
        something went wrong.
        """
        all_events: List[Event] = []
        for element in action_requests:
            logger.debug(f"Action map contains the following actions: {action_map}.")
            action = action_map.get(element["action"])
            if action is None:
                raise ViewsException(f"Action {element['action']} does not exist.")
            logger.debug(f"Perform action {element['action']}.")
            events = action(self.permission_adapter, self.database_adapter).perform(
                element["data"], self.user_id
            )
            logger.debug(f"Prepared events {events}.")
            all_events.extend(events)
        logger.debug("All events ready.")
        return all_events

    def handle_error(self, exception: CustomException, status_code: int) -> None:
        """
        Handles some exceptions during dispatch of request. Raises HTTP 400 or
        HTTP 403.
        """
        logger.debug(
            f"Error in view. Status code: {status_code}. Exception message: {exception.message}"
        )
        if status_code == 400:
            raise ViewsException(exception.message)
        elif status_code == 403:
            raise PermissionDenied(exception.message)
        raise RuntimeError("This line should never be reached.")
