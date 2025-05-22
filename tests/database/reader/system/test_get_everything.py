from unittest.mock import MagicMock

from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from tests.database.reader.system.util import (
    setup_data,
    standard_data,
    standard_responses,
)


def test_simple(db_connection: Connection) -> None:
    setup_data(db_connection, standard_data)
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        response = extended_database.get_everything()
    assert response == standard_responses
