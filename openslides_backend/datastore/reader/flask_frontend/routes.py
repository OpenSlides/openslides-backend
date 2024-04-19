from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import fastjsonschema

from openslides_backend.datastore.reader.core.requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetEverythingRequest,
    GetManyRequest,
    GetRequest,
    HistoryInformationRequest,
    MinMaxRequest,
)
from openslides_backend.datastore.shared.flask_frontend import (
    InvalidRequest,
    build_url_prefix,
    unify_urls,
)
from openslides_backend.datastore.shared.postgresql_backend.sql_query_helper import (
    VALID_AGGREGATE_CAST_TARGETS,
)
from openslides_backend.datastore.shared.util import DeletedModelsBehaviour
from openslides_backend.shared.filters import filter_definitions_schema

URL_PREFIX = build_url_prefix("reader")


class Route(str, Enum):
    GET = "get"
    GET_MANY = "get_many"
    GET_ALL = "get_all"
    GET_EVERYTHING = "get_everything"
    FILTER = "filter"
    EXISTS = "exists"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    HISTORY_INFORMATION = "history_information"

    @property
    def URL(self):
        return unify_urls(URL_PREFIX, self.value)


deleted_models_behaviour_list = list(
    behaviour.value for behaviour in DeletedModelsBehaviour
)


get_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "fqid": {"type": "string"},
            "position": {"type": "integer"},
            "mapped_fields": {"type": "array", "items": {"type": "string"}},
            "get_deleted_models": {
                "type": "integer",
                "enum": deleted_models_behaviour_list,
            },
        },
        "required": ["fqid"],
    }
)


get_many_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "requests": {
                "oneOf": [
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "collection": {"type": "string"},
                                "ids": {"type": "array", "items": {"type": "integer"}},
                                "mapped_fields": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["collection", "ids"],
                        },
                    },
                    {"type": "array", "items": {"type": "string"}},
                ],
            },
            "position": {"type": "integer"},
            "mapped_fields": {"type": "array", "items": {"type": "string"}},
            "get_deleted_models": {
                "type": "integer",
                "enum": deleted_models_behaviour_list,
            },
        },
        "required": ["requests"],
    }
)

get_all_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "collection": {"type": "string"},
            "mapped_fields": {"type": "array", "items": {"type": "string"}},
            "get_deleted_models": {
                "type": "integer",
                "enum": deleted_models_behaviour_list,
            },
        },
        "required": ["collection"],
    }
)

get_everything_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "get_deleted_models": {
                "type": "integer",
                "enum": deleted_models_behaviour_list,
            },
        },
    }
)

filter_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "$defs": filter_definitions_schema,
        "properties": {
            "collection": {"type": "string"},
            "filter": {"$ref": "#/$defs/filter"},
            "mapped_fields": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["collection", "filter"],
    }
)

aggregate_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "$defs": filter_definitions_schema,
        "properties": {
            "collection": {"type": "string"},
            "filter": {"$ref": "#/$defs/filter"},
        },
        "required": ["collection", "filter"],
    }
)

minmax_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "$defs": filter_definitions_schema,
        "properties": {
            "collection": {"type": "string"},
            "filter": {"$ref": "#/$defs/filter"},
            "field": {"type": "string"},
            "type": {"type": "string", "enum": VALID_AGGREGATE_CAST_TARGETS},
        },
        "required": ["collection", "filter", "field"],
    }
)

history_information_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "fqids": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["fqids"],
    }
)


def handle_filter_schema_error(e: fastjsonschema.JsonSchemaException) -> None:
    if e.rule == "anyOf":
        # we only use anyOf for filters, so an invalid filter definition was given
        raise InvalidRequest(f"Invalid filter definition: {e.value}")


@dataclass
class RouteConfiguration:
    schema: Callable
    request_class: type
    schema_error_handler: None | (
        Callable[[fastjsonschema.JsonSchemaException], None]
    ) = None


# maps all available routes to the respective schema
route_configurations: dict[Route, RouteConfiguration] = {
    Route.GET: RouteConfiguration(schema=get_schema, request_class=GetRequest),
    Route.GET_MANY: RouteConfiguration(
        schema=get_many_schema, request_class=GetManyRequest
    ),
    Route.GET_ALL: RouteConfiguration(
        schema=get_all_schema, request_class=GetAllRequest
    ),
    Route.GET_EVERYTHING: RouteConfiguration(
        schema=get_everything_schema, request_class=GetEverythingRequest
    ),
    Route.FILTER: RouteConfiguration(
        schema=filter_schema,
        request_class=FilterRequest,
        schema_error_handler=handle_filter_schema_error,
    ),
    Route.EXISTS: RouteConfiguration(
        schema=aggregate_schema,
        request_class=AggregateRequest,
        schema_error_handler=handle_filter_schema_error,
    ),
    Route.COUNT: RouteConfiguration(
        schema=aggregate_schema,
        request_class=AggregateRequest,
        schema_error_handler=handle_filter_schema_error,
    ),
    Route.MIN: RouteConfiguration(
        schema=minmax_schema,
        request_class=MinMaxRequest,
        schema_error_handler=handle_filter_schema_error,
    ),
    Route.MAX: RouteConfiguration(
        schema=minmax_schema,
        request_class=MinMaxRequest,
        schema_error_handler=handle_filter_schema_error,
    ),
    Route.HISTORY_INFORMATION: RouteConfiguration(
        schema=history_information_schema,
        request_class=HistoryInformationRequest,
    ),
}
