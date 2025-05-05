import datetime
import zoneinfo
from decimal import Decimal
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

expected_response_changed_models = {
    1: {"username": "3", "default_vote_weight": Decimal("42")},
    2: {"username": "3", "default_vote_weight": Decimal("23")},
    4: {"username": "3", "default_vote_weight": None},
}
last_login_filter = FilterOperator(
    "last_login",
    "=",
    datetime.datetime(2012, 5, 31, 0, 0, tzinfo=zoneinfo.ZoneInfo(key="Etc/UTC")),
)


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
        response = extended_database.filter(
            collection, filter_, mapped_fields, use_changed_models=False
        )
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
    base_test(db_connection, "user", FilterOperator("username", "%=", "DAt%"), 1)


@pytest.mark.parametrize(
    "filter_,to_be_found_id",
    [
        pytest.param(FilterOperator("id", "=", 1), 1, id="int_equal"),
        pytest.param(FilterOperator("id", "!=", 0), "all", id="int_not_equal"),
        pytest.param(FilterOperator("id", "<", 2), 1, id="int_smaller"),
        pytest.param(FilterOperator("id", "<=", 3), "all", id="int_smaller_equal"),
        pytest.param(FilterOperator("id", ">", 2), 3, id="int_greater"),
        pytest.param(FilterOperator("id", ">=", 1), "all", id="int_greater_equal"),
        pytest.param(FilterOperator("is_demo_user", "=", False), 2, id="bool"),
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
        pytest.param(
            And(
                FilterOperator("username", "=", "daren"),
                FilterOperator("username", "=", "daren"),
            ),
            2,
            id="and",
        ),
        pytest.param(
            Or(
                FilterOperator("username", "=", "data"),
                FilterOperator("username", "=", "daren"),
                FilterOperator("first_name", "=", "nerad"),
            ),
            "all",
            id="or",
        ),
        pytest.param(
            Or(
                And(
                    FilterOperator("username", "=", "daren"),
                    FilterOperator("first_name", "=", "daren"),
                ),
                Not(
                    Or(
                        FilterOperator("username", "=", "data"),
                        FilterOperator("first_name", "=", "nerad"),
                    )
                ),
            ),
            2,
            id="complex",
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
    base_test(db_connection, "user", FilterOperator("last_name", "!=", None), 2)


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


@pytest.mark.parametrize(
    "filter_,to_be_found_ids",
    [
        pytest.param(last_login_filter, [2], id="operator"),
        pytest.param(FilterOperator("last_login", "=", None), [1, 4], id="none_db"),
        pytest.param(FilterOperator("meeting_ids", "!=", None), [2, 4], id="none_changed"),
        pytest.param(
            FilterOperator("meeting_ids", "has", 3), [2, 4], id="none_with_has"
        ),
        pytest.param(Not(last_login_filter), [1, 4], id="not"),
        pytest.param(Not(FilterOperator("username", "=", "3")), [], id="not_name"),
        pytest.param(
            Not(Not(FilterOperator("username", "=", "3"))), [1, 2, 4], id="not_not"
        ),
        pytest.param(
            And(
                FilterOperator("username", "=", "3"),
                FilterOperator("is_demo_user", "=", True),
            ),
            [1, 2],
            id="and_simple",
        ),
        pytest.param(
            And(
                FilterOperator("username", "=", "3"),
                FilterOperator("default_vote_weight", "=", "42.000000"),
            ),
            [1],
            id="and_split",
        ),
        pytest.param(
            Or(
                FilterOperator("username", "=", "3"),
                FilterOperator("first_name", "=", "daren"),
            ),
            [1, 2, 4],
            id="or",
        ),
        pytest.param(
            Not(
                Or(
                    FilterOperator("meeting_ids", "=", [1, 2, 3]),
                    FilterOperator("first_name", "=", "daren"),
                )
            ),
            [1, 4],
            id="not_or",
        ),
        pytest.param(
            Not(
                Or(
                    FilterOperator("meeting_ids", "=", None),
                    FilterOperator("first_name", "=", "daren"),
                )
            ),
            [4],
            id="not_or_split_unmatched",
        ),
        pytest.param(
            Not(
                Or(
                    FilterOperator("meeting_ids", "=", [1, 3]),
                    FilterOperator("default_vote_weight", "=", "81"),
                )
            ),
            [1, 4],
            id="not_or_split_matched",
        ),
        pytest.param(
            Not(
                And(
                    FilterOperator("meeting_ids", "=", None),
                    FilterOperator("default_vote_weight", "=", "42"),
                )
            ),
            [2, 4],
            id="not_and_split_unmatched",
        ),
        pytest.param(
            Not(
                And(
                    FilterOperator("meeting_ids", "=", None),
                    FilterOperator("default_vote_weight", "=", "23"),
                )
            ),
            [1, 2, 4],
            id="not_and_split_matched",
        ),
        pytest.param(
            Or(
                And(FilterOperator("username", "=", "3"), Not(last_login_filter)),
                Not(
                    Or(
                        FilterOperator("default_vote_weight", ">=", "23"),
                        FilterOperator("default_vote_weight", "<=", "42"),
                    )
                ),
            ),
            [1, 4],
            id="complex",
        ),
    ],
)
def test_changed_models(
    db_connection: Connection, filter_: Filter, to_be_found_ids: list[int]
) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        ex_db = ExtendedDatabase(conn, MagicMock(), MagicMock())
        ex_db.apply_changed_model("user/1", {"username": "3", "meeting_ids": None})
        ex_db.apply_changed_model("user/2", {"username": "3", "is_demo_user": True})
        ex_db.apply_changed_model("user/3", {"meta_deleted": True})
        ex_db.apply_changed_model(
            "user/4", {"username": "3", "meta_new": True, "meeting_ids": [3]}
        )
        response = ex_db.filter("user", filter_, ["username", "default_vote_weight"])
    for id_ in response:
        assert id_ in to_be_found_ids
    for id_ in to_be_found_ids:
        assert id_ in response
        assert response[id_] == expected_response_changed_models[id_]


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
