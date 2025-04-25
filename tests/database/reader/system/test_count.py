from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import InvalidFormat
from openslides_backend.shared.filters import Filter, FilterOperator
from openslides_backend.shared.patterns import Collection
from tests.database.reader.system.util import setup_data, standard_data


@pytest.mark.parametrize(
    "filter_,expected_count",
    [
        pytest.param(FilterOperator("name", "=", "non-exist4nt"), 0, id="non-existent"),
        pytest.param(FilterOperator("name", "=", "23"), 1, id="exists"),
        pytest.param(FilterOperator("id", "=", 1), 1, id="int"),
        pytest.param(None, 2, id="without filter"),
    ],
)
def test_basic(db_connection: Connection, filter_: Filter, expected_count: int) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.count(
            "committee", filter_, use_changed_models=False
        )
    assert response == expected_count


@pytest.mark.parametrize(
    "collection,filter_,expected_error",
    [
        pytest.param(
            "committeee",
            None,
            "Collection 'committeee' does not exist in the database:",
            id="collection_no_filter",
        ),
        pytest.param(
            "committeee",
            FilterOperator("name", "=", "23"),
            "Collection 'committeee' does not exist in the database:",
            id="collection",
        ),
        pytest.param(
            "committee",
            FilterOperator("namee", "=", "23"),
            "Field 'namee' does not exist in collection 'committee': column",
            id="field",
        ),
    ],
)
def test_invalid(
    db_connection: Connection,
    collection: Collection,
    filter_: Filter,
    expected_error: str,
) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        with pytest.raises(InvalidFormat) as e:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.count(collection, filter_, use_changed_models=False)
    assert expected_error in e.value.msg


def test_changed_models(db_connection: Connection) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.changed_models["committee/1"].update({"name": "3"})
        extended_database.changed_models["committee/4"].update({"name": "3"})
        response = extended_database.count(
            "committee", FilterOperator("name", "=", "3")
        )
    assert response == 2
