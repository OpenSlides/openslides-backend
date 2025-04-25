from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import InvalidFormat
from openslides_backend.shared.filters import (
    And,
    Filter,
    FilterLiteral,
    FilterOperator,
    Not,
    Or,
)
from openslides_backend.shared.patterns import Id
from openslides_backend.shared.typing import Model
from tests.database.reader.system.util import (
    setup_data,
    standard_data,
    standard_responses,
)
from tests.database.util import TestPerformance, performance


def base_test(
    db_connection: Connection,
    collection: str,
    filter_: Filter,
    to_be_found_id: int | str,
    mapped_fields: list[str] = [],
) -> dict[Id, Model]:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.filter(collection, filter_, mapped_fields)
    if isinstance(to_be_found_id, int):
        assert response == {
            to_be_found_id: standard_responses[collection][to_be_found_id]
        }
    elif to_be_found_id == "all":
        assert response == standard_responses[collection]
    return response


@pytest.mark.parametrize(
    "filter_operator,filter_value,to_be_found_id",
    [
        ("=", "23", 1),
        (">", "23", 2),
        (">", "21", "all"),
        (">=", "23", "all"),
        ("!=", "23", 2),
        ("<", "42", 1),
        ("<=", "42", "all"),
        pytest.param("%=", "4%", 2, id="%=-4%-2 - ilike"),
        pytest.param("%=", "%2%", "all", id="%=-%2%-all - ilike_multiple_matches"),
    ],
)
def test_filters(
    db_connection: Connection,
    filter_operator: FilterLiteral,
    filter_value: str | int,
    to_be_found_id: int | str,
) -> None:
    base_test(
        db_connection,
        "committee",
        FilterOperator("name", filter_operator, filter_value),
        to_be_found_id,
    )


def test_eq_ignore_case(db_connection: Connection) -> None:
    base_test(db_connection, "user", FilterOperator("username", "~=", "DATA"), 1)


def test_ilike_case_insensitive(db_connection: Connection) -> None:
    base_test(db_connection, "user", FilterOperator("username", "%=", "DA%"), "all")


@pytest.mark.parametrize(
    "filter_,to_be_found_id",
    [
        pytest.param(FilterOperator("id", "=", 1), 1, id="int_equal"),
        pytest.param(FilterOperator("id", "!=", 1), 2, id="int_not_equal"),
        pytest.param(FilterOperator("id", "<", 2), 1, id="int_smaller"),
        pytest.param(FilterOperator("id", "<=", 2), "all", id="int_smaller_equal"),
        pytest.param(FilterOperator("id", ">", 1), 2, id="int_greater"),
        pytest.param(FilterOperator("id", ">=", 1), "all", id="int_greater_equal"),
        pytest.param(FilterOperator("is_demo_user", "=", True), 1, id="bool"),
        pytest.param(FilterOperator("meeting_ids", "=", [1, 3]), 2, id="list[int]"),
        pytest.param(FilterOperator("last_login", "=", "2012/05/31"), 2, id="date"),
        pytest.param(
            FilterOperator("default_vote_weight", "=", "42.000000"), 1, id="decimal"
        ),
        pytest.param(
            FilterOperator("default_vote_weight", "=", 42), 1, id="decimal_with_int"
        ),
    ],
)
def test_types(db_connection: Connection, filter_: Filter, to_be_found_id: int) -> None:
    base_test(db_connection, "user", filter_, to_be_found_id)


@pytest.mark.parametrize(
    "filter_,to_be_found_id",
    [
        (
            And(
                FilterOperator("username", "=", "daren"),
                FilterOperator("username", "=", "daren"),
            ),
            2,
        ),
        (
            Or(
                FilterOperator("username", "=", "data"),
                FilterOperator("username", "=", "daren"),
            ),
            "all",
        ),
        (
            Or(
                And(
                    FilterOperator("username", "=", "daren"),
                    FilterOperator("username", "=", "daren"),
                ),
                Not(
                    Or(
                        FilterOperator("username", "=", "data"),
                        FilterOperator("username", "=", "daren"),
                    )
                ),
            ),
            2,
        ),
    ],
)
def test_logic_filters(
    db_connection: Connection, filter_: Filter, to_be_found_id: int
) -> None:
    base_test(db_connection, "user", filter_, to_be_found_id)


def test_eq_none(db_connection: Connection) -> None:
    base_test(db_connection, "user", FilterOperator("first_name", "=", None), 1)


def test_neq_none(db_connection: Connection) -> None:
    base_test(db_connection, "user", FilterOperator("first_name", "!=", None), 2)


def test_mapped_fields(db_connection: Connection) -> None:
    response = base_test(
        db_connection,
        "user",
        FilterOperator("username", "=", "data"),
        "no_check",
        ["meeting_ids", "username", "first_name"],
    )
    assert response == {
        1: {"first_name": None, "meeting_ids": [1, 2, 3], "username": "data"}
    }


def test_invalid_mapped_fields() -> None:
    with get_new_os_conn() as conn:
        with pytest.raises(InvalidFormat) as e:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.filter(
                "user",
                FilterOperator("username", "=", "data"),
                ["first_name", "not valid"],
            )
    assert "Invalid fields: ['not valid']" in e.value.msg


def test_invalid_mapped_fields2() -> None:
    with get_new_os_conn() as conn:
        with pytest.raises(InvalidFormat) as e:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.filter(
                "user",
                FilterOperator("username", "=", "data"),
                ["first_name", "not_valid"],
            )
    assert (
        "Field 'not_valid' does not exist in collection 'user': column" in e.value.msg
    )
    assert "\nCheck mapped fields." in e.value.msg


def test_invalid_collection(db_connection: Connection) -> None:
    with pytest.raises(InvalidFormat) as e:
        base_test(db_connection, "usarr", FilterOperator("username", "=", "data"), 0)
    assert "Collection 'usarr' does not exist in the database:" in e.value.msg


def test_invalid_filter_field(db_connection: Connection) -> None:
    with pytest.raises(InvalidFormat) as e:
        base_test(db_connection, "user", FilterOperator("usarrname", "=", "data"), 0)
    assert (
        "Field 'usarrname' does not exist in collection 'user': column" in e.value.msg
    )
    assert "\nCheck filter fields." in e.value.msg


def test_changed_models(db_connection: Connection) -> None:
    # TODO this could be erroneous
    # need complex Filter test too
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.changed_models["committee/1"].update({"name": "3"})
        response = extended_database.filter(
            "committee", FilterOperator("name", "=", "3"), []
        )
    assert response == {1: {"name": "3"}}


@performance
def test_like_performance(db_connection: Connection) -> None:
    print("\nPreparing ..\n")
    MODEL_COUNT = 100000
    data = {
        "user": {
            i: {"username": f"{i}", "first_name": "2", "meeting_ids": [3]}
            for i in range(1, MODEL_COUNT + 1)
        }
    }
    setup_data(db_connection, data)

    print("\nEqual:\n")
    with get_new_os_conn() as conn:
        with TestPerformance(conn) as performance:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            result = extended_database.filter(
                "user", FilterOperator("username", "=", "1337"), ["first_name"]
            )
    print(f"{performance['total_time']} seconds")
    print(f"requests: {performance['requests_count']}")
    print(
        f"read time: {performance['read_time']}, write time: {performance['write_time']}"
    )
    assert len(result)

    print("\nLike:\n")
    with get_new_os_conn() as conn:
        with TestPerformance(conn) as performance:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            result = extended_database.filter(
                "user",
                FilterOperator("username", "%=", f"%{MODEL_COUNT - 1}%"),
                ["first_name"],
            )
    print(f"{performance['total_time']} seconds")
    print(f"requests: {performance['requests_count']}")
    print(
        f"read time: {performance['read_time']}, write time: {performance['write_time']}"
    )
    assert len(result)

    print("\nLike many:\n")
    with get_new_os_conn() as conn:
        with TestPerformance(conn) as performance:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            result = extended_database.filter(
                "user", FilterOperator("username", "%=", "%1337%"), ["first_name"]
            )
    print(f"{performance['total_time']} seconds")
    print(f"requests: {performance['requests_count']}")
    print(
        f"read time: {performance['read_time']}, write time: {performance['write_time']}"
    )
    assert len(result)
