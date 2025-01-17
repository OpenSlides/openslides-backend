import json

from openslides_backend.datastore.reader.flask_frontend.routes import Route
from openslides_backend.datastore.shared.flask_frontend.errors import ERROR_CODES
from openslides_backend.services.database.event_types import EVENT_TYPE
from tests.datastore.reader.system.util import setup_data
from tests.datastore.util import assert_error_response, assert_success_response

FQID = "collection/1"
data = {
    "fqid": FQID,
    "field_1": "data",
    "field_2": 42,
    "field_3": [1, 2, 3],
    "meta_position": 1,
    "meta_deleted": False,
}
data_json = json.dumps(data)


def test_simple(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, {FQID: data})
    response = json_client.post(Route.GET.URL, {"fqid": FQID})
    assert_success_response(response)
    assert response.json == data


def test_no_model(json_client, db_connection, db_cur):
    response = json_client.post(Route.GET.URL, {"fqid": FQID})
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_get_no_deleted_success(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, {FQID: data})
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID},
    )
    assert_success_response(response)
    assert response.json == data


def test_get_no_deleted_fail(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, {FQID: data}, True)
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID},
    )
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, {FQID: data})
    response = json_client.post(
        Route.GET.URL, {"fqid": FQID, "mapped_fields": ["fqid", "field_3"]}
    )
    assert_success_response(response)
    assert response.json == {
        "fqid": FQID,
        "field_3": [1, 2, 3],
    }


def test_too_many_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, {FQID: data})
    fields = [f"field_{i}" for i in range(2000)]
    response = json_client.post(Route.GET.URL, {"fqid": FQID, "mapped_fields": fields})
    assert_success_response(response)
    assert response.json == {
        "field_1": "data",
        "field_2": 42,
        "field_3": [1, 2, 3],
    }


def test_mapped_fields_filter_none_values(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, {FQID: data})
    response = json_client.post(
        Route.GET.URL, {"fqid": FQID, "mapped_fields": ["field_that_doesnt_exist"]}
    )
    assert_success_response(response)
    assert response.json == {}


def setup_events_data(connection, cursor):
    cursor.execute(
        "insert into positions (user_id, migration_index) values"
        + " (0, 1), (0, 1), (0, 1), (0, 1), (0, 1)"
    )
    cursor.execute(
        "insert into events (position, fqid, type, data, weight) values (1, %s, %s, %s, 1)",
        [FQID, EVENT_TYPE.CREATE, data_json],
    )
    cursor.execute(
        "insert into events (position, fqid, type, data, weight) values (2, %s, %s, %s, 2)",
        [FQID, EVENT_TYPE.UPDATE, json.dumps({"field_1": "other"})],
    )
    connection.commit()


def test_position(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    response = json_client.post(Route.GET.URL, {"fqid": FQID, "position": 1})
    assert_success_response(response)
    assert response.json == data


def test_current_position(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    response = json_client.post(Route.GET.URL, {"fqid": FQID, "position": 2})
    assert_success_response(response)
    assert response.json["field_1"] == "other"


def test_position_deleted(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    db_cur.execute(
        "insert into events (position, fqid, type, weight) values (3, %s, %s, 3)",
        [FQID, EVENT_TYPE.DELETE],
    )
    db_connection.commit()
    response = json_client.post(Route.GET.URL, {"fqid": FQID, "position": 3})
    assert_error_response(response, ERROR_CODES.MODEL_DOES_NOT_EXIST)


def test_position_mapped_fields(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET.URL, {"fqid": FQID, "position": 1, "mapped_fields": ["field_1"]}
    )
    assert_success_response(response)
    assert response.json == {"field_1": "data"}


def test_position_mapped_fields_filter_none_values(json_client, db_connection, db_cur):
    setup_events_data(db_connection, db_cur)
    response = json_client.post(
        Route.GET.URL,
        {"fqid": FQID, "position": 1, "mapped_fields": ["field_that_doesnt_exist"]},
    )
    assert_success_response(response)
    assert response.json == {}


def test_order(json_client, db_connection, db_cur):
    """
    4 events within 2 positions - Note that the events are created in reverse
    (see the weight and position). Make sure, that they are ordered correctly
    by position and weight.
    """
    db_cur.execute(
        "insert into positions (user_id, migration_index) values" + " (0, 1), (0, 1)"
    )
    # Do not reorder - the ids are implicitly chosen form 1-4
    db_cur.execute(
        "insert into events (position, fqid, type, data, weight) values (2, %s, %s, %s, 2)",
        [FQID, EVENT_TYPE.RESTORE, json.dumps(None)],
    )
    db_cur.execute(
        "insert into events (position, fqid, type, data, weight) values (2, %s, %s, %s, 1)",
        [FQID, EVENT_TYPE.DELETE, json.dumps(None)],
    )
    db_cur.execute(
        "insert into events (position, fqid, type, data, weight) values (1, %s, %s, %s, 2)",
        [FQID, EVENT_TYPE.UPDATE, json.dumps({"field_1": "other"})],
    )
    db_cur.execute(
        "insert into events (position, fqid, type, data, weight) values (1, %s, %s, %s, 1)",
        [FQID, EVENT_TYPE.CREATE, data_json],
    )
    db_connection.commit()

    response = json_client.post(Route.GET.URL, {"fqid": FQID, "position": 2})
    assert_success_response(response)
    assert response.json["field_1"] == "other"


def test_invalid_fqid(json_client):
    response = json_client.post(Route.GET.URL, {"fqid": "not valid"})
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_mapped_fields(json_client):
    response = json_client.post(
        Route.GET.URL, {"fqid": FQID, "mapped_fields": ["not valid"]}
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_position(json_client):
    response = json_client.post(Route.GET.URL, {"fqid": FQID, "position": 0})
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_empty_payload(json_client):
    response = json_client.post(Route.GET.URL, None)
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
