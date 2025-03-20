from unittest.mock import MagicMock

import pytest
from psycopg import Connection

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import ModelDoesNotExist
from openslides_backend.shared.interfaces.event import EventType
from tests.database.writer.system.util import (
    assert_no_model,
    create_model,
    create_write_requests,
    get_data,
)


def test_single_delete(db_connection: Connection) -> None:
    data = get_data()
    create_model(data)
    fqid = "user/1"

    data[0]["events"] = [{"type": EventType.Delete, "fqid": fqid}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_no_model(fqid)


def test_delete_model_does_not_exist(db_connection: Connection) -> None:
    fqid = "user/1"
    data = get_data()
    data[0]["events"] = [{"type": EventType.Delete, "fqid": fqid}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(ModelDoesNotExist) as e_info:
            extended_database.write(create_write_requests(data))
    assert e_info.value.fqid == "user/1"
    assert_no_model(fqid)
