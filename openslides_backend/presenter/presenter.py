from typing import Callable, Dict, Type

import fastjsonschema  # type: ignore
from fastjsonschema import JsonSchemaException  # type: ignore

from ..shared.exceptions import PresenterException
from ..shared.handlers import Base as HandlerBase
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter_interface import Payload, PresenterResponse

presenters_map: Dict[str, Type[BasePresenter]] = {}


def register_presenter(
    name: str,
) -> Callable[[Type[BasePresenter]], Type[BasePresenter]]:
    """
    Decorator to be used for presenter classes. Registers the class so that it
    can be found by the handler.
    """

    def wrapper(clazz: Type[BasePresenter]) -> Type[BasePresenter]:
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


class PresenterHandler(HandlerBase):
    """
    Presenter handler. It is the concret implementation of Presenter interface.
    """

    def handle_request(self, payload: Payload, user_id: int) -> PresenterResponse:
        """
        Takes payload and user id and handles this request by validating and
        parsing the presentations.
        """

        # Validate payload of request
        try:
            self.validate(payload)
        except JsonSchemaException as exception:
            raise PresenterException(exception.message)

        # Parse presentations and creates response
        response = self.parse_presenters(payload)
        self.logger.debug("Request was successful. Send response now.")
        return response

    def validate(self, payload: Payload) -> None:
        """
        Validates presenter requests sent by client. Raises JsonSchemaException if
        input is invalid.
        """
        self.logger.debug("Validate presenter request.")
        payload_schema(payload)

    def parse_presenters(self, payload: Payload) -> PresenterResponse:
        """
        Parses presenter request send by client. Raises PresenterException
        if something went wrong.
        """
        # permissions = self.permission().get_all(self.user_id)
        self.logger.debug(
            f"Presenter map contains the following presenters: {presenters_map}."
        )
        response = []
        for presenter_blob in payload:
            PresenterClass = presenters_map.get(presenter_blob["presenter"])
            if PresenterClass is not None:
                presenter_instance = PresenterClass(
                    presenter_blob.get("data"),
                    self.permission,
                    self.database,
                    self.logging,
                )
                presenter_instance.validate()
                result = presenter_instance.get_result()
                response.append(result)
            else:
                raise PresenterException(
                    f"Presenter {presenter_blob['presenter']} does not exist."
                )
        self.logger.debug("Presenter data ready.")
        return response
