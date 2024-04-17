from openslides_backend.datastore.reader.flask_frontend.routes import Route
from openslides_backend.datastore.shared.flask_frontend import ERROR_CODES
from tests.datastore import assert_error_response
from tests.datastore.reader.system.util import setup_data
from tests.datastore.util import TestPerformance, assert_success_response, performance

data = {
    "a/1": {
        "field_1": "data",
        "field_2": 42,
        "field_3": True,
        "field_not_none": 1,
        "meta_position": 1,
    },
    "a/2": {"field_1": "test", "field_2": 21, "field_3": False, "meta_position": 2},
    "b/1": {
        "field_4": "data",
        "field_5": 42,
        "field_6": True,
        "meta_position": 3,
    },
}


def test_eq(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "=", "value": "data"},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"1": data["a/1"]}, "position": 3}


def test_gt(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_2", "operator": ">", "value": 21},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"1": data["a/1"]}, "position": 3}


def test_gt_with_high_string_value(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_2", "operator": ">", "value": 9},
        },
    )
    assert_success_response(response)
    assert response.json == {
        "data": {"1": data["a/1"], "2": data["a/2"]},
        "position": 3,
    }


def test_geq(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_2", "operator": ">=", "value": 21},
        },
    )
    assert_success_response(response)
    assert response.json == {
        "data": {"1": data["a/1"], "2": data["a/2"]},
        "position": 3,
    }


def test_neq(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_2", "operator": "!=", "value": 21},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"1": data["a/1"]}, "position": 3}


def test_lt(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_2", "operator": "<", "value": 42},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"2": data["a/2"]}, "position": 3}


def test_leq(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_2", "operator": "<=", "value": 42},
        },
    )
    assert_success_response(response)
    assert response.json == {
        "data": {"1": data["a/1"], "2": data["a/2"]},
        "position": 3,
    }


def test_eq_ignore_case(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "~=", "value": "DATA"},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"1": data["a/1"]}, "position": 3}


def test_like(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "%=", "value": "dat%"},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"1": data["a/1"]}, "position": 3}


def test_like_multiple_matches(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "%=", "value": "%t%"},
        },
    )
    assert_success_response(response)
    assert response.json == {
        "data": {"1": data["a/1"], "2": data["a/2"]},
        "position": 3,
    }


def test_like_case_insensitive(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "%=", "value": "DAT%"},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"1": data["a/1"]}, "position": 3}


@performance
def test_like_performance(json_client, db_connection, db_cur):
    MODEL_COUNT = 100000
    setup_data(
        db_connection,
        db_cur,
        {
            f"c/{i}": {"field_1": f"data{i}", "field_2": i, "meta_position": i + 1}
            for i in range(MODEL_COUNT)
        },
    )
    with TestPerformance() as perf_equal:
        response = json_client.post(
            Route.FILTER.URL,
            {
                "collection": "c",
                "filter": {"field": "field_1", "operator": "=", "value": "data4242"},
            },
        )
    assert_success_response(response)
    assert len(response.json["data"]) == 1

    with TestPerformance() as perf_like:
        response = json_client.post(
            Route.FILTER.URL,
            {
                "collection": "c",
                "filter": {
                    "field": "field_1",
                    "operator": "%=",
                    "value": f"%{MODEL_COUNT - 1}%",
                },
            },
        )
    assert_success_response(response)
    assert len(response.json["data"]) == 1

    with TestPerformance() as perf_like_many:
        response = json_client.post(
            Route.FILTER.URL,
            {
                "collection": "c",
                "filter": {"field": "field_1", "operator": "%=", "value": "%ta42%"},
            },
        )
    assert_success_response(response)

    print(f"Equal: {perf_equal['total_time']} seconds")
    print(f"Like: {perf_like['total_time']} seconds")
    print(f"Like with many results: {perf_like_many['total_time']} seconds")


def test_and(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {
                "and_filter": [
                    {"field": "field_1", "operator": "=", "value": "data"},
                    {"field": "field_2", "operator": "=", "value": 42},
                ]
            },
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"1": data["a/1"]}, "position": 3}


def test_or(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {
                "or_filter": [
                    {"field": "field_1", "operator": "=", "value": "data"},
                    {"field": "field_1", "operator": "=", "value": "test"},
                ]
            },
        },
    )
    assert_success_response(response)
    assert response.json == {
        "data": {"1": data["a/1"], "2": data["a/2"]},
        "position": 3,
    }


def test_complex(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    # (field_1 == 'data' and field_2 > 21) or (field_3 == False and not field_2 < 21)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {
                "or_filter": [
                    {
                        "and_filter": [
                            {"field": "field_1", "operator": "=", "value": "data"},
                            {"field": "field_2", "operator": ">", "value": 21},
                        ]
                    },
                    {
                        "and_filter": [
                            {"field": "field_3", "operator": "=", "value": False},
                            {
                                "not_filter": {
                                    "field": "field_2",
                                    "operator": "<",
                                    "value": 21,
                                }
                            },
                        ]
                    },
                ],
            },
        },
    )
    assert_success_response(response)
    assert response.json == {
        "data": {"1": data["a/1"], "2": data["a/2"]},
        "position": 3,
    }


def test_eq_none(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_not_none", "operator": "=", "value": None},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"2": data["a/2"]}, "position": 3}


def test_neq_none(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_not_none", "operator": "!=", "value": None},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {"1": data["a/1"]}, "position": 3}


def test_empty_field(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "empty", "operator": "=", "value": "data"},
        },
    )
    assert_success_response(response)
    assert response.json == {"data": {}, "position": 3}


def test_mapped_fields(json_client, db_connection, db_cur):
    setup_data(db_connection, db_cur, data)
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field_1", "operator": "=", "value": "data"},
            "mapped_fields": ["field_3", "meta_position"],
        },
    )
    assert_success_response(response)
    assert response.json == {
        "data": {"1": {"field_3": True, "meta_position": 1}},
        "position": 3,
    }


def test_invalid_collection(json_client):
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "not valid",
            "filter": {"field": "field", "operator": "=", "value": "data"},
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_mapped_fields(json_client):
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field", "operator": "=", "value": "data"},
            "mapped_fields": ["not valid"],
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_field(json_client):
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "not valid", "operator": "=", "value": "data"},
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_FORMAT)


def test_invalid_operator(json_client):
    response = json_client.post(
        Route.FILTER.URL,
        {
            "collection": "a",
            "filter": {"field": "field", "operator": "invalid", "value": "data"},
        },
    )
    assert_error_response(response, ERROR_CODES.INVALID_REQUEST)
