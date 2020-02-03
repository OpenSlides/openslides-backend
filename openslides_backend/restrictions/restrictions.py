from typing import Any, Callable, Dict, Type

import fastjsonschema  # type: ignore
from fastjsonschema import JsonSchemaException  # type: ignore

from ..shared.exceptions import RestrictionException
from ..shared.interfaces import LoggingModule, Services
from ..shared.patterns import KEYSEPARATOR, Collection, FullQualifiedField
from ..shared.schema import schema_version
from .restrictions_interface import Payload, RestrictionResponse

Restriction = Any  # TODO


def prepare_restrictions_map() -> None:
    """
    This function just imports all restrictions modules so that the restrictions
    are recognized by the system and the register decorator can do its work.

    New modules have to be added here.
    """
    # from . import meeting, topic  # type: ignore # noqa
    pass


restrictions_map: Dict[Collection, Type[Restriction]] = {}


def register_restriction(
    name: Collection,
) -> Callable[[Type[Restriction]], Type[Restriction]]:
    """
    Decorator to be used for restriction classes. Registers the class so that it
    can be found by the handler.
    """

    def wrapper(restriction: Type[Restriction]) -> Type[Restriction]:
        restrictions_map[name] = restriction
        return restriction

    return wrapper


prepare_restrictions_map()


payload_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Schema for restrictions API",
        "description": "An array of restriction blobs, i. e. bundles of user_id and full qualified fields.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "user_id": {
                    "description": "Id of the user the given fields should be restricted for.",
                    "type": "integer",
                    "mininmum": 0,
                },
                "fqfields": {
                    "description": "An array of strings in the format of full qualified fields.",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": f"^[a-z][a-z0-9_]*{KEYSEPARATOR}[1-9][0-9]*{KEYSEPARATOR}[a-z][a-z0-9_]*$",
                    },
                    "minItems": 1,
                    "uniqueItems": True,
                },
            },
            "required": ["user_id", "fqfields"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


class RestrictionsHandler:
    """
    Restrictions handler. It is the concret implementation of Restrictions interface.
    """

    def handle_request(
        self, payload: Payload, logging: LoggingModule, services: Services,
    ) -> RestrictionResponse:
        """
        Takes payload and user id and handles this request by validating and
        parsing all fields. The fields are restricted according to the user id.
        """
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        self.permission = services.permission
        self.database = services.database

        # Validate payload of request
        try:
            self.validate(payload)
        except JsonSchemaException as exception:
            raise RestrictionException(exception.message)

        # Parse restrictions and creates response
        response = self.parse_restrictions(payload)
        self.logger.debug("Request was successful. Send response now.")
        return response

    def validate(self, payload: Payload) -> None:
        """
        Validates restrictions requests sent by client. Raises JsonSchemaException if
        input is invalid.
        """
        self.logger.debug("Validate restrictions request.")
        payload_schema(payload)

    def parse_restrictions(self, payload: Payload) -> RestrictionResponse:
        """
        Parses restrictions request send by client. Raises RestrictionException
        if something went wrong.
        """
        # permissions = self.permission().get_all(self.user_id)
        self.logger.debug(
            f"Restrictions map contains the following restrictions: {restrictions_map}."
        )
        response = []
        for restriction_blob in payload:
            # user_id = restriction_blob["user_id"]
            blob_response = {}
            for key in restriction_blob["fqfields"]:
                collection_str, id, field = key.split(KEYSEPARATOR)
                fqfield = FullQualifiedField(Collection(collection_str), int(id), field)
                # restriction = restrictions_map.get(fqfield.collection)
                # if restriction is None:
                #     raise RestrictionException(
                #         f"Restriction for {str(fqfield.collection)} does not exist."
                #     )
                # self.logger.debug(f"Perform restriction for {fqfield}.")
                # blob_response[fqfield] = restriction(permissions, self.database()).perform(
                #     fqfield, self.user_id
                # )
                blob_response[fqfield] = self.dummy_restriction()
            response.append(blob_response)
        self.logger.debug("Restricted data ready.")
        return response

    def dummy_restriction(self) -> Any:
        # Just a dummy restrictor, that restricts nothing but always send the same message.
        return "This is a restricted field content made by dummy restrictor."
