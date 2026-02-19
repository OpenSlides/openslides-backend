from collections.abc import Callable

import fastjsonschema
from fastjsonschema import JsonSchemaException

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)

from ..http.request import Request
from ..shared.exceptions import PresenterException
from ..shared.handlers.base_handler import BaseHandler
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter_interface import Payload, PresenterResponse

presenters_map: dict[str, type[BasePresenter]] = {}


def register_presenter(
    name: str,
) -> Callable[[type[BasePresenter]], type[BasePresenter]]:
    """
    Decorator to be used for presenter classes. Registers the class so that it
    can be found by the handler.
    """

    def wrapper(clazz: type[BasePresenter]) -> type[BasePresenter]:
        presenters_map[name] = clazz
        return clazz

    return wrapper


payload_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Schema for presenter API",
        "description": "An array of presenter blobs, i. e. bundles of user_id and presentation.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "presenter": {
                    "description": "The name of the presenter.",
                    "type": "string",
                    "minLength": 1,
                },
                "data": {"description": "The data", "type": "object"},
            },
            "required": ["presenter"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


class PresenterHandler(BaseHandler):
    """
    Presenter handler. It is the concret implementation of Presenter interface.
    """

    def handle_request(self, request: Request, user_id: int) -> PresenterResponse:
        """
        Takes payload and user id and handles this request by validating and
        parsing the presentations.
        """
        # Validate payload of request
        try:
            self.validate(request.json)
        except JsonSchemaException as exception:
            raise PresenterException(exception.message)

        # Parse presentations and creates response
        with get_new_os_conn() as conn:
            self.datastore = ExtendedDatabase(conn, self.logging, self.env)
            response = self.parse_presenters(request, user_id)
        self.logger.debug("Request was successful. Send response now.")
        return response

    def validate(self, payload: Payload) -> None:
        """
        Validates presenter requests sent by client. Raises JsonSchemaException if
        input is invalid.
        """
        self.logger.debug("Validate presenter request.")
        payload_schema(payload)

    def parse_presenters(
        self, request: Request, user_id: int
    ) -> PresenterResponse:
        """
        Parses presenter request send by client. Raises PresenterException
        if something went wrong.
        """
        self.logger.debug(
            f"Presenter map contains the following presenters: {presenters_map}."
        )
        presenters = []
        for presenter_blob in request.json:
            presenter = presenters_map.get(presenter_blob["presenter"])
            if presenter is None:
                raise PresenterException(
                    f"Presenter {presenter_blob['presenter']} does not exist."
                )
            presenters.append(presenter)

        response = []
        for PresenterClass in presenters:
            presenter_instance = PresenterClass(
                presenter_blob.get("data"),
                self.services,
                self.datastore,
                self.logging,
                user_id,
            )
            presenter_instance.validate()
            # with self.datastore.get_database_context():
            result = presenter_instance.get_result()
            response.append(result)
        self.logger.debug("Presenter data ready.")
        return response
