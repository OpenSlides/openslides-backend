from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.writer.postgresql_backend import (
    BaseDbEvent,
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbListUpdateEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)


def test_base_db_event_get_modified_fields():
    with pytest.raises(NotImplementedError):
        BaseDbEvent("a/1").get_modified_fields()


def test_base_db_event_get_event_data():
    with pytest.raises(NotImplementedError):
        BaseDbEvent("a/1").get_event_data()


def test_db_create_event():
    fqid = MagicMock()
    value = MagicMock()
    field_data = {"my_key": value}

    event = DbCreateEvent(fqid, field_data)

    assert event.fqid == fqid
    assert "my_key" in event.field_data

    modified_fields = event.get_modified_fields()
    assert "my_key" in modified_fields


def test_db_update_event():
    fqid = MagicMock()
    value = MagicMock()
    field_data = {"my_key": value}

    event = DbUpdateEvent(fqid, field_data)

    assert event.fqid == fqid
    assert "my_key" in event.field_data

    modified_fields = event.get_modified_fields()
    assert "my_key" in modified_fields


def test_db_list_update_event():
    fqid = MagicMock()
    value = MagicMock()
    add = {"my_key": value}
    remove = {"other_key": value}
    model = {"other_key": []}

    event = DbListUpdateEvent(fqid, add, remove, model)
    assert model == {"other_key": []}  # do not change

    assert event.fqid == fqid
    assert "my_key" in event.add
    assert "other_key" in event.remove

    modified_fields = event.get_modified_fields()
    assert "my_key" in modified_fields
    assert "other_key" in modified_fields


def test_db_list_update_event_nothing_on_empty_remove():
    fqid = MagicMock()
    value = MagicMock()
    remove = {"not_existing": value}
    model = {}

    event = DbListUpdateEvent(fqid, {}, remove, model)
    assert model == {}  # do not change

    modified_fields = event.get_modified_fields()
    assert modified_fields == {}


def test_db_delete_fields_event():
    fqid = MagicMock()
    field = MagicMock()

    event = DbDeleteFieldsEvent(fqid, [field])

    assert event.fqid == fqid
    assert event.fields == [field]
    assert event.get_modified_fields() == {field: None}


def test_db_delete_event():
    fqid = MagicMock()
    field = MagicMock()

    event = DbDeleteEvent(fqid, [field])

    assert event.fqid == fqid
    assert event.get_modified_fields() == {field: None}


def test_db_delete_event_set_modified_fields():
    field = MagicMock()

    event = DbDeleteEvent(None, [field])

    assert event.get_modified_fields() == {field: None}


def test_db_restore_event():
    fqid = MagicMock()
    field = MagicMock()

    event = DbRestoreEvent(fqid, [field])

    assert event.fqid == fqid
    assert event.get_modified_fields() == {field: None}


def test_db_restore_event_set_modified_fields():
    field = MagicMock()

    event = DbRestoreEvent(None, [field])

    assert event.get_modified_fields() == {field: None}
