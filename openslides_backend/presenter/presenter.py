from collections.abc import Callable

import fastjsonschema
from authlib import AUTHENTICATION_HEADER, COOKIE_NAME
from fastjsonschema import JsonSchemaException

from ..http.request import Request
from ..shared.exceptions import PresenterException
from ..shared.handlers.base_handler import BaseHandler
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter_interface import Payload, PresenterResponse

presenters_map: dict[str, type[BasePresenter]] = {}


def register_presenter(
    name: str,
    csrf_exempt: bool = False,
) -> Callable[[type[BasePresenter]], type[BasePresenter]]:
    """
    Decorator to be used for presenter classes. Registers the class so that it
    can be found by the handler.
    """

    def wrapper(clazz: type[BasePresenter]) -> type[BasePresenter]:
        clazz.csrf_exempt = csrf_exempt
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

    def handle_request(self, request: Request) -> tuple[PresenterResponse, str | None]:
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
        response, access_token = self.parse_presenters(request)
        self.logger.debug("Request was successful. Send response now.")
        return response, access_token

    def validate(self, payload: Payload) -> None:
        """
        Validates presenter requests sent by client. Raises JsonSchemaException if
        input is invalid.
        """
        self.logger.debug("Validate presenter request.")
        payload_schema(payload)

    def parse_presenters(
        self, request: Request
    ) -> tuple[PresenterResponse, str | None]:
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

        if len({presenter.csrf_exempt for presenter in presenters}) > 1:
            raise PresenterException(
                "You cannot call presenters with different login mechanisms"
            )

        self.services.authentication().set_authentication(
            request.headers.get(AUTHENTICATION_HEADER, ""),
            request.cookies.get(COOKIE_NAME, ""),
        )
        access_token: str | None = None
        if presenters[0].csrf_exempt:
            user_id = self.services.authentication().authenticate_only_refresh_id()
        else:
            user_id, access_token = self.services.authentication().authenticate()

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
            with self.datastore.get_database_context():
                result = presenter_instance.get_result()
            response.append(result)
        self.logger.debug("Presenter data ready.")
        return response, access_token
