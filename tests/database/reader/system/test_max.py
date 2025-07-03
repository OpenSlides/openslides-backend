from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import InvalidFormat
from openslides_backend.shared.filters import Filter, FilterOperator
from openslides_backend.shared.patterns import Collection, Field
from tests.database.reader.system.util import setup_data, standard_data


@pytest.mark.parametrize(
    "collection,filter_,field,to_be_found_max",
    [
        pytest.param("user", FilterOperator("id", "<", 2), "id", 1, id="single"),
        pytest.param("user", FilterOperator("id", "<=", 2), "id", 2, id="multiple"),
        pytest.param("user", None, "id", 3, id="collection"),
        pytest.param(
            "committee", FilterOperator("id", "<=", 2), "name", "42", id="text"
        ),
        pytest.param(
            "committee", FilterOperator("id", ">=", 3), "name", None, id="no_result"
        ),
    ],
)
def test_basic(
    db_connection: Connection,
    collection: Collection,
    filter_: Filter,
    field: Field,
    to_be_found_max: int | None,
) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.max(
            collection, filter_, field, use_changed_models=False
        )
    assert response == to_be_found_max


@pytest.mark.parametrize(
    "collection,filter_,field,expected_error",
    [
        pytest.param(
            "committeee",
            FilterOperator("name", "=", "23"),
            "name",
            "Collection 'committeee' does not exist in the database:",
            id="collection",
        ),
        pytest.param(
            "user",
            FilterOperator("id", "<=", 2),
            "not valid",
            "Field 'not valid' does not exist in collection 'user': column",
            id="field",
        ),
        pytest.param(
            "committee",
            FilterOperator("namee", "=", "23"),
            "name",
            "Field 'namee' does not exist in collection 'committee': column",
            id="filter_field",
        ),
    ],
)
def test_invalid(
    db_connection: Connection,
    collection: Collection,
    filter_: Filter,
    field: str,
    expected_error: str,
) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        with pytest.raises(InvalidFormat) as e:
            extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
            extended_database.max(collection, filter_, field, use_changed_models=False)
    assert expected_error in e.value.message


def test_changed_models(db_connection: Connection) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.apply_changed_model("committee/1", {"name": "3"})
        extended_database.apply_changed_model(
            "committee/4", {"name": "5", "meta_new": True}
        )
        response = extended_database.max(
            "committee", FilterOperator("name", "=", "3"), "name"
        )
    assert response == "3"
