from typing import Any

import fastjsonschema
from dacite import Config, from_dict
from dacite.exceptions import MissingValueError

from openslides_backend.datastore.reader.core import Reader
from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.flask_frontend import InvalidRequest
from openslides_backend.datastore.shared.util import BadCodingError, logger
from openslides_backend.shared.typing import JSON

from .routes import Route, route_configurations


class JSONHandler:
    def handle_request(self, route: Route, data: JSON) -> dict:
        """
        A generic handler for all requests. Parses the request to a python object
        according to the route_setup and execute the according route_handler.
        """

        try:
            route_configuration = route_configurations[route]
        except KeyError:
            raise BadCodingError("Invalid route metadata: " + route)

        logger.info(f"{route.upper()}-request: {data}")

        try:
            request_data = route_configuration.schema(data)
        except fastjsonschema.JsonSchemaException as e:
            if route_configuration.schema_error_handler:
                route_configuration.schema_error_handler(e)
            raise InvalidRequest(e.message)

        try:
            request_object: Any = from_dict(
                route_configuration.request_class,
                request_data,
                Config(check_types=False),
            )
        except (TypeError, MissingValueError) as e:
            raise BadCodingError("Invalid data to initialize class\n" + str(e))

        reader = injector.get(Reader)
        route_handler = getattr(reader, route)

        with reader.get_database_context():
            return route_handler(request_object)
