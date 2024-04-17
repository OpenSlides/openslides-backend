from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend.sql_query_helper import (
    SqlQueryHelper,
)
from openslides_backend.datastore.shared.services.read_database import (
    AggregateFilterQueryFieldsParameters,
    CountFilterQueryFieldsParameters,
    MappedFieldsFilterQueryFieldsParameters,
)
from openslides_backend.datastore.shared.util import BadCodingError, InvalidFormat
from openslides_backend.shared.filters import And, FilterOperator, Not, Or
from tests.datastore import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register(SqlQueryHelper, SqlQueryHelper)
    yield


@pytest.fixture()
def query_helper(provide_di):
    yield injector.get(SqlQueryHelper)


def test_build_filter_query_mapped_fields(query_helper: SqlQueryHelper):
    query_helper.build_filter_str = bfs = MagicMock(return_value=MagicMock())
    filter = MagicMock()
    param = MappedFieldsFilterQueryFieldsParameters(["field"])

    q, a, s = query_helper.build_filter_query(MagicMock(), filter, param)

    assert bfs.call_args[0] == (filter, [])
    assert a[0] == "field"
    assert s == ["field"]


def test_build_filter_query_invalid_function(query_helper: SqlQueryHelper):
    query_helper.build_filter_str = bfs = MagicMock(return_value=MagicMock())
    filter = MagicMock()
    param = AggregateFilterQueryFieldsParameters("invalid", "field", "int")

    with pytest.raises(BadCodingError):
        query_helper.build_filter_query(MagicMock(), filter, param)

    assert bfs.call_args[0] == (filter, [])


def test_build_filter_query_invalid_cast_target(query_helper: SqlQueryHelper):
    query_helper.build_filter_str = bfs = MagicMock(return_value=MagicMock())
    filter = MagicMock()
    param = AggregateFilterQueryFieldsParameters("min", "field", "invalid")

    with pytest.raises(BadCodingError):
        query_helper.build_filter_query(MagicMock(), filter, param)

    assert bfs.call_args[0] == (filter, [])


def test_build_filter_query_aggregate(query_helper: SqlQueryHelper):
    query_helper.build_filter_str = bfs = MagicMock(return_value=MagicMock())
    filter = MagicMock()
    field = MagicMock()
    param = AggregateFilterQueryFieldsParameters("min", field, "int")

    q, a, s = query_helper.build_filter_query(MagicMock(), filter, param)

    assert bfs.call_args[0] == (filter, [])
    assert a[0] == field
    assert s == []


def test_build_filter_query_count(query_helper: SqlQueryHelper):
    query_helper.build_filter_str = bfs = MagicMock(return_value=MagicMock())
    filter = MagicMock()
    param = CountFilterQueryFieldsParameters()

    q, a, s = query_helper.build_filter_query(MagicMock(), filter, param)

    assert bfs.call_args[0] == (filter, [])
    assert s == []


def test_build_filter_query_invalid_fields_params(query_helper: SqlQueryHelper):
    query_helper.build_filter_str = MagicMock(return_value=MagicMock())
    filter = MagicMock()
    param = "invalid"

    with pytest.raises(BadCodingError):
        query_helper.build_filter_query(MagicMock(), filter, param)


def test_build_filter_str_not(query_helper: SqlQueryHelper):
    f = query_helper.build_filter_str
    query_helper.build_filter_str = MagicMock(return_value="")
    filter = Not(MagicMock())

    assert f(filter, []) == "NOT ()"


def test_build_filter_str_or(query_helper: SqlQueryHelper):
    f = query_helper.build_filter_str
    query_helper.build_filter_str = MagicMock(return_value="")
    filter = Or([MagicMock(), MagicMock()])

    assert f(filter, []) == "() OR ()"


def test_build_filter_str_and(query_helper: SqlQueryHelper):
    f = query_helper.build_filter_str
    query_helper.build_filter_str = MagicMock(return_value="")
    filter = And([MagicMock(), MagicMock()])

    assert f(filter, []) == "() AND ()"


def test_build_filter_str_invalid(query_helper: SqlQueryHelper):
    with pytest.raises(BadCodingError):
        query_helper.build_filter_str("invalid", [])


def test_build_filter_str_none(query_helper: SqlQueryHelper):
    filter = FilterOperator("field", "!=", None)
    args = []
    assert query_helper.build_filter_str(filter, args) == "data->>%s IS NOT NULL"
    assert args == ["field"]


def test_build_filter_str_none_invalid(query_helper: SqlQueryHelper):
    filter = FilterOperator("field", ">", None)
    with pytest.raises(InvalidFormat):
        query_helper.build_filter_str(filter, [])


def test_build_filter_str_filter_operator(query_helper: SqlQueryHelper):
    f = query_helper.build_filter_str
    query_helper.build_filter_str = MagicMock(return_value="")
    filter = FilterOperator("f", "=", 0)

    assert f(filter, [], "a") == "a.data->>%s = %s::text"
