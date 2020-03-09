from typing import Any, Callable, Dict, Type

import fastjsonschema  # type: ignore
from fastjsonschema import JsonSchemaException  # type: ignore

from ..shared.exceptions import PresenterException
from ..shared.interfaces import LoggingModule, Services
from ..shared.patterns import Collection
from ..shared.schema import schema_version
from .presenter_interface import Payload, PresenterResponse

Presentation = Any  # TODO: Add a base.py and implement a base Presenter class.


def prepare_presentations_map() -> None:
    """
    This function just imports all presentation modules so that the presentations
    are recognized by the system and the register decorator can do its work.

    New modules have to be added here.
    """
    # from . import meeting, topic  # type: ignore # noqa
    pass


presentations_map: Dict[Collection, Type[Presentation]] = {}


def register_presentation(
    name: Collection,
) -> Callable[[Type[Presentation]], Type[Presentation]]:
    """
    Decorator to be used for presentation classes. Registers the class so that
    it can be found by the handler.
    """

    def wrapper(presentation: Type[Presentation]) -> Type[Presentation]:
        presentations_map[name] = presentation
        return presentation

    return wrapper


prepare_presentations_map()


payload_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Schema for presenter API",
        "description": "An array of presenter blobs, i. e. bundles of user_id and presentation.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "user_id": {
                    "description": "Id of the user the presentation should be for.",
                    "type": "integer",
                    "mininmum": 0,
                },
                "presentation": {
                    "description": "The name of the presentation.",
                    "type": "string",
                    "minLength": 1,
                },
            },
            "required": ["user_id", "presentation"],
            "additionalProperties": False,
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


class PresenterHandler:
    """
    Presenter handler. It is the concret implementation of Presenter interface.
    """

    def handle_request(
        self, payload: Payload, logging: LoggingModule, services: Services,
    ) -> PresenterResponse:
        """
        Takes payload and user id and handles this request by validating and
        parsing the presentations.
        """
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        self.permission = services.permission
        self.database = services.database

        # Validate payload of request
        try:
            self.validate(payload)
        except JsonSchemaException as exception:
            raise PresenterException(exception.message)

        # Parse presentations and creates response
        response = self.parse_presentations(payload)
        self.logger.debug("Request was successful. Send response now.")
        return response

    def validate(self, payload: Payload) -> None:
        """
        Validates presenter requests sent by client. Raises JsonSchemaException if
        input is invalid.
        """
        self.logger.debug("Validate presenter request.")
        payload_schema(payload)

    def parse_presentations(self, payload: Payload) -> PresenterResponse:
        """
        Parses presenter request send by client. Raises PresenterException
        if something went wrong.
        """
        # permissions = self.permission().get_all(self.user_id)
        self.logger.debug(
            f"Presentations map contains the following presentations: {presentations_map}."
        )
        response = []
        for presentation_blob in payload:
            # user_id = presentation_blob["user_id"]
            if presentation_blob["presentation"] == "dummy":
                response.append(self.dummy_presentation())
            else:
                raise PresenterException(
                    f"Presentation {presentation_blob['presentation']} does not exist."
                )
        self.logger.debug("Presentation data ready.")
        return response

    def dummy_presentation(self) -> Any:
        # Just a dummy presentation.
        return {"dummy": "dummy"}
