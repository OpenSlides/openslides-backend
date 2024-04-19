from typing import Any, cast

from flask import request

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.flask_frontend import (
    InvalidRequest,
    JsonResponse,
    add_health_route,
    dev_only_route,
    handle_internal_errors,
)
from openslides_backend.datastore.writer.core import Writer
from openslides_backend.datastore.writer.flask_frontend.routes import (  # noqa
    DELETE_HISTORY_INFORMATION_URL,
    RESERVE_IDS_URL,
    TRUNCATE_DB_URL,
    WRITE_URL,
    WRITE_WITHOUT_EVENTS_URL,
)
from openslides_backend.shared.patterns import collection_from_fqid

from .json_handlers import ReserveIdsHandler, WriteHandler


@handle_internal_errors
def write():
    if not request.is_json:
        raise InvalidRequest("Data must be json")

    write_handler = WriteHandler()
    write_handler.write(request.get_json())
    return "", 201


@handle_internal_errors
def reserve_ids():
    if not request.is_json:
        raise InvalidRequest("Data must be json")

    reserve_ids_handler = ReserveIdsHandler()
    ids = reserve_ids_handler.reserve_ids(request.get_json())
    return JsonResponse({"ids": ids})


@handle_internal_errors
def write_without_events():
    if not request.is_json:
        raise InvalidRequest("Data must be json")
    if not isinstance(request.json, list):
        raise InvalidRequest("write_without_events data internally must be a list!")
    req_json = cast(list[dict[str, Any]], request.json)[0]
    if len(req_json.get("events", ())) != 1 and any(
        event["type"] != "delete" for event in req_json.get("events", ())
    ):
        raise InvalidRequest("write_without_events may contain only 1 event!")
    if any(
        collection_from_fqid(event["fqid"]) not in ["action_worker", "import_preview"]
        for event in req_json.get("events", ())
    ):
        raise InvalidRequest(
            "Collection for write_without_events must be action_worker or import_preview"
        )
    write_handler = WriteHandler()
    write_handler.write_without_events(req_json)
    return_code = 200 if req_json.get("events", ())[0]["type"] == "delete" else 201
    return ("", return_code)


@dev_only_route
@handle_internal_errors
def truncate_db():
    writer = injector.get(Writer)
    writer.truncate_db()
    return "", 204


@handle_internal_errors
def delete_history_information():
    writer = injector.get(Writer)
    writer.delete_history_information()
    return "", 204


def register_routes(app, url_prefix):
    for route in (
        "write",
        "reserve_ids",
        "delete_history_information",
        "truncate_db",
        "write_without_events",
    ):
        app.add_url_rule(
            globals()[f"{route.upper()}_URL"],
            route,
            globals()[route],
            methods=["POST"],
            strict_slashes=False,
        )
    add_health_route(app, url_prefix)
