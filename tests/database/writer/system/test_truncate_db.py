from unittest.mock import MagicMock

from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.interfaces.event import EventType
from tests.database.writer.system.util import assert_no_model, create_model, get_data


def test_truncate_simple(db_connection: Connection) -> None:
    data = get_data()
    create_model(data)
    fqid = "user/1"

    data[0]["events"] = [{"type": EventType.Delete, "fqid": fqid}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.truncate_db()
        assert extended_database.reserve_id("user") == 1
    assert_no_model(fqid)
