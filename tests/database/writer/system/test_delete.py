from unittest.mock import MagicMock

import pytest

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.exceptions import ModelDoesNotExist
from openslides_backend.shared.interfaces.event import EventType
from tests.database.writer.system.test_create import test_create_nm_field_simple
from tests.database.writer.system.util import (
    assert_model,
    assert_no_model,
    create_models,
    create_write_requests,
    get_data,
)


def test_single_delete() -> None:
    data = get_data()
    create_models(data)
    fqid = "user/1"

    data[0]["events"] = [{"type": EventType.Delete, "fqid": fqid}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_no_model(fqid)


def test_delete_model_does_not_exist() -> None:
    fqid = "user/1"
    data = get_data()
    data[0]["events"] = [{"type": EventType.Delete, "fqid": fqid}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        with pytest.raises(ModelDoesNotExist) as e_info:
            extended_database.write(create_write_requests(data))
    assert e_info.value.fqid == "user/1"
    assert_no_model(fqid)


def test_delete_nm() -> None:
    test_create_nm_field_simple()
    fqid = "user/1"

    data = [{"events": [{"type": EventType.Delete, "fqid": fqid}]}]
    with get_new_os_conn() as conn:
        extended_database = ExtendedDatabase(conn, MagicMock(), MagicMock())
        extended_database.write(create_write_requests(data))
    assert_no_model(fqid)
    assert_model("committee/1", {"id": 1, "name": "com1", "user_ids": None})
