from dataclasses import dataclass
from typing import Any, TypedDict, cast

import fastjsonschema

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.flask_frontend import InvalidRequest
from openslides_backend.datastore.shared.util import (
    BadCodingError,
    SelfValidatingDataclass,
)
from openslides_backend.datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
    Writer,
    WriteRequest,
)
from openslides_backend.datastore.writer.core.write_request import LockedFieldsJSON
from openslides_backend.shared.filters import filter_definitions_schema
from openslides_backend.shared.patterns import Collection
from openslides_backend.shared.typing import JSON

collectionfield_lock_with_filter_schema = {
    "type": "object",
    "properties": {
        "position": {"type": "integer"},
        "filter": {"$ref": "#/$defs/filter"},
    },
    "required": ["position"],
}

write_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$defs": filter_definitions_schema,
        "type": "object",
        "properties": {
            "user_id": {"type": "integer"},
            "information": {},
            "locked_fields": {
                "type": "object",
                "additionalProperties": {
                    **collectionfield_lock_with_filter_schema,
                    "type": ["integer", "object", "array"],
                    "items": collectionfield_lock_with_filter_schema,
                    "minItems": 1,
                },
            },
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["create", "update", "delete", "restore"],
                        },
                        "fqid": {"type": "string"},
                    },
                    "required": ["type", "fqid"],
                },
            },
            "migration_index": {"type": "integer", "minimum": 1},
        },
        "required": ["user_id", "information", "locked_fields", "events"],
    }
)


update_event_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "type": {},
            "fqid": {},
            "fields": {
                "type": "object",
            },
            "list_fields": {
                "type": "object",
                "properties": {
                    "add": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {"type": ["integer", "string"]},
                        },
                    },
                    "remove": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {"type": ["integer", "string"]},
                        },
                    },
                },
                "additionalProperties": False,
            },
        },
        "required": ["type", "fqid"],
        "additionalProperties": False,
    }
)


class WriteRequestJSON(TypedDict):
    user_id: int
    information: JSON
    locked_fields: dict[str, LockedFieldsJSON]
    events: list[dict[str, Any]]
    migration_index: int | None


class WriteHandler:
    def write(self, data: JSON) -> None:
        if not isinstance(data, list):
            data = [data]

        write_requests = []
        for request in data:
            write_requests.append(self.build_write_request(request))

        writer = injector.get(Writer)
        writer.write(write_requests)

    def write_without_events(self, data: JSON) -> None:
        write_request = self.build_write_request(data)

        writer = injector.get(Writer)
        writer.write_without_events(write_request)

    def build_write_request(self, data: JSON) -> WriteRequest:
        try:
            parsed_data = cast(WriteRequestJSON, write_schema(data))
        except fastjsonschema.JsonSchemaException as e:
            raise InvalidRequest(e.message)

        user_id = parsed_data["user_id"]
        information = parsed_data["information"]
        locked_fields = parsed_data["locked_fields"]
        events = self.parse_events(parsed_data["events"])
        migration_index = parsed_data.get("migration_index")

        return WriteRequest(
            events, information, user_id, locked_fields, migration_index
        )

    def parse_events(self, events: list[dict[str, Any]]) -> list[BaseRequestEvent]:
        request_events = []
        for event in events:
            type = event["type"]

            if type == "create":
                fields = event.get("fields")
                if not isinstance(fields, dict):
                    raise InvalidRequest("Fields must be a dict")

            if type == "update":
                try:
                    update_event_schema(event)
                except fastjsonschema.JsonSchemaException as e:
                    raise InvalidRequest(e.message)

            request_events.append(self.create_event(event))
        return request_events

    def create_event(self, event: dict[str, Any]) -> BaseRequestEvent:
        type = event["type"]
        fqid = event["fqid"]
        request_event: BaseRequestEvent
        if type == "create":
            request_event = RequestCreateEvent(fqid, event["fields"])
        elif type == "update":
            request_event = RequestUpdateEvent(
                fqid, event.get("fields", {}), event.get("list_fields", {})
            )
        elif type == "delete":
            request_event = RequestDeleteEvent(fqid)
        elif type == "restore":
            request_event = RequestRestoreEvent(fqid)
        else:
            raise BadCodingError()
        return request_event


reserve_ids_schema = fastjsonschema.compile(
    {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "amount": {"type": "integer"},
            "collection": {"type": "string"},
        },
        "required": ["amount", "collection"],
    }
)


@dataclass
class ReserveIdsRequestJSON(SelfValidatingDataclass):
    collection: Collection
    amount: int


class ReserveIdsHandler:
    def reserve_ids(self, data: JSON) -> list[int]:
        try:
            parsed_data = ReserveIdsRequestJSON(**reserve_ids_schema(data))
        except fastjsonschema.JsonSchemaException as e:
            raise InvalidRequest(e.message)

        writer = injector.get(Writer)
        return writer.reserve_ids(parsed_data.collection, parsed_data.amount)
