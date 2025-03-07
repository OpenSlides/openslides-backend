from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import ModelLocked
from openslides_backend.shared.interfaces.event import EventType
# import datastore.shared.util.otel as otel
# from datastore.shared.di import injector
# from datastore.shared.flask_frontend import ERROR_CODES
# from datastore.shared.postgresql_backend import ConnectionHandler
# from datastore.writer.core import Messaging
# from datastore.writer.flask_frontend.routes import WRITE_URL
# from tests.util import assert_error_response, assert_response_code
# from tests.writer.system.util import (
#     assert_model,
#     assert_modified_fields,
#     assert_no_modified_fields,
#     get_redis_modified_fields,
#     setup_otel,
# )
from tests.database.writer.system.util import (
    assert_model,
    create_model,
    create_write_requests,
    get_data,
)


def test_two_write_requests_with_locked_fields(db_connection: Connection) -> None:
    # TODO does this really make sense? TO mee it seems like we shouldn't even need to send locks on writes
    # TODO this probably needs two async threads to actually have conflicts
    # TODO doesn't use fqfields yet
    data = get_data()
    create_model(data)
    data = [
        {
            "events": [
                {
                    "type": EventType.Update,
                    "fqid": "user/1",
                    "fields": {"username": "None", "first_name": None},
                }
            ]
        },
        {
            "events": [
                {
                    "type": EventType.Update,
                    "fqid": "user/1",
                    "fields": {"username": "Some", "last_name": "1"},
                }
            ],
            "locked_fields": True,  # {"user/1/first_name": "Some"}}
        },
    ]

    with pytest.raises(ModelLocked) as e_info:
        with get_new_os_conn() as conn:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.write(create_write_requests(data))
    assert_model(
        "user/1", {"id": 1, "username": "Some", "first_name": None, "last_name": "1"}
    )
    assert e_info.value.keys == "first_name"

    # create_model(json_client, data, redis_connection, reset_redis_data)

    # data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    # data2 = copy.deepcopy(data)
    # data2["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f2": 1}}
    # data2["locked_fields"] = {"a/1/f": 1}
    # response = json_client.post(WRITE_URL, [data, data2])
    # assert_model("a/1", {"f": 1}, 1)
    # assert_error_response(response, ERROR_CODES.MODEL_LOCKED)
    # assert_no_modified_fields(redis_connection)


# def test_otel(json_client, data, redis_connection):
#     setup_otel()
#     response = json_client.post(WRITE_URL, data)
#     assert_response_code(response, 201)
#     assert otel.OTEL_DATA_FIELD_KEY in get_redis_modified_fields(redis_connection)
