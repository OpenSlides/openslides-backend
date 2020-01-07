from typing import Dict, Iterable, List

from fastjsonschema import JsonSchemaException  # type: ignore
from werkzeug.exceptions import BadRequest, Forbidden
from werkzeug.wrappers import Response

from .. import logging
from ..actions.action_map import action_map
from ..adapters.authentication import AuthenticationAdapter
from ..adapters.database import DatabaseAdapter
from ..adapters.event_store import EventStoreAdapter
from ..adapters.permission import PermissionAdapter
from ..adapters.providers import (
    AuthenticationProvider,
    DatabaseProvider,
    EventStoreProvider,
    PermissionProvier,
)
from ..exceptions import (
    ActionException,
    AuthException,
    BackendBaseException,
    EventStoreException,
    MediaTypeException,
    PermissionDenied,
)
from ..utils.types import Environment, Event
from .schema import action_view_schema
from .wrappers import Request

logger = logging.getLogger(__name__)


class ActionView:
    """
    During initialization we bind the viewpoint and services to the instance.
    """

    def __init__(self, environment: Environment) -> None:
        self.authentication_adapter: AuthenticationProvider = AuthenticationAdapter(
            environment["authentication_url"]
        )
        self.permission_adapter: PermissionProvier = PermissionAdapter(
            environment["permission_url"]
        )
        self.database_adapter: DatabaseProvider = DatabaseAdapter(
            environment["database_url"]
        )
        self.event_store_adapter: EventStoreProvider = EventStoreAdapter(
            environment["event_store_url"]
        )

    def dispatch(self, request: Request, **kwargs: dict) -> Response:
        """
        Dispatches request to the viewpoint.
        """
        logger.debug("Start dispatching request.")

        # Get request user id
        try:
            self.user_id = self.authentication_adapter.get_user(request)
        except AuthException as exception:
            self.handle_error(exception, 400)

        # Validate payload of request
        if not request.is_json:
            self.handle_error(
                MediaTypeException(
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
        return Response()

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
                raise BadRequest(f"Action {element['action']} does not exist.")
            logger.debug(f"Perform action {element['action']}.")
            events = action(self.permission_adapter, self.database_adapter).perform(
                element["data"], self.user_id
            )
            logger.debug(f"Prepared events {events}.")
            all_events.extend(events)
        logger.debug("All events ready.")
        return events

    def handle_error(self, exception: BackendBaseException, status_code: int) -> None:
        """
        Handles some exceptions during dispatch of request. Raises HTTP 400 or
        HTTP 403.
        """
        logger.debug(
            f"Error in view. Status code: {status_code}. Exception message: {exception.message}"
        )
        if status_code == 400:
            raise BadRequest(exception.message)
        elif status_code == 403:
            raise Forbidden(exception.message)
        raise RuntimeError("This line should never be reached.")
