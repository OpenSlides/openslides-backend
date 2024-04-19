from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.shared.util import (
    BadCodingError,
    ModelDoesNotExist,
    ModelExists,
    ModelNotDeleted,
)
from openslides_backend.datastore.writer.core import (
    RequestCreateEvent,
    RequestDeleteEvent,
    RequestRestoreEvent,
    RequestUpdateEvent,
)
from openslides_backend.datastore.writer.postgresql_backend import (
    DbCreateEvent,
    DbDeleteEvent,
    DbDeleteFieldsEvent,
    DbListUpdateEvent,
    DbRestoreEvent,
    DbUpdateEvent,
)
from openslides_backend.datastore.writer.postgresql_backend.event_translator import (
    EventTranslator,
    EventTranslatorService,
)
from openslides_backend.shared.patterns import META_DELETED
from tests.datastore import reset_di  # noqa


@pytest.fixture()
def event_translator(reset_di):  # noqa
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register(EventTranslator, EventTranslatorService)
    yield injector.get(EventTranslator)


@pytest.fixture()
def request_events():
    yield [
        RequestCreateEvent("a/1", {"a": 1}),
        RequestDeleteEvent("b/2"),
        RequestUpdateEvent("a/1", {"a": None, "b": [1, True]}),
        RequestRestoreEvent("b/2"),
    ]


def test_creation(event_translator):
    assert bool(event_translator)


def test_translate_create(event_translator, request_events):
    event = RequestCreateEvent("a/1", {"a": 1})
    db_events = event_translator.translate(event, MagicMock())
    assert len(db_events) == 1
    assert isinstance(db_events[0], DbCreateEvent)
    assert db_events[0].fqid == "a/1"
    assert db_events[0].field_data == {"a": 1}


def test_translate_create_fqid_exists(event_translator, request_events):
    event = RequestCreateEvent("a/1", {"a": 1})
    with pytest.raises(ModelExists):
        event_translator.translate(event, {"a/1": {}})


def test_translate_update(event_translator, request_events):
    event = RequestUpdateEvent(
        "a/1", {"a": None, "b": [1, True]}, {"add": {"c": [1]}, "remove": {"d": [2]}}
    )
    db_events = event_translator.translate(
        event, {"a/1": {META_DELETED: False, "d": [2]}}
    )
    assert len(db_events) == 3
    assert isinstance(db_events[0], DbUpdateEvent)
    assert isinstance(db_events[1], DbDeleteFieldsEvent)
    assert isinstance(db_events[2], DbListUpdateEvent)
    assert db_events[0].fqid == "a/1"
    assert db_events[0].field_data == {"b": [1, True]}
    assert db_events[1].fqid == "a/1"
    assert db_events[1].fields == ["a"]
    assert db_events[2].fqid == "a/1"
    assert db_events[2].add == {"c": [1]}
    assert db_events[2].remove == {"d": [2]}
    assert db_events[2].get_modified_fields() == {"c": [1], "d": []}


def test_update_no_delete_fields_event(event_translator):
    update_event = RequestUpdateEvent("a/1", {"a": "some_value"})

    db_events = event_translator.translate(update_event, {"a/1": {META_DELETED: False}})

    assert len(db_events) == 1
    assert isinstance(db_events[0], DbUpdateEvent)


def test_translate_update_fqid_non_existent(event_translator, request_events):
    event = RequestUpdateEvent("a/1", {"a": 1})
    with pytest.raises(ModelDoesNotExist):
        event_translator.translate(event, {})


def test_translate_update_fqid_deleted(event_translator, request_events):
    event = RequestUpdateEvent("a/1", {"a": 1})
    with pytest.raises(ModelDoesNotExist):
        event_translator.translate(event, {"a/1": {META_DELETED: True}})


def test_translate_delete(event_translator, request_events):
    event = RequestDeleteEvent("a/1")
    db_events = event_translator.translate(event, {"a/1": {META_DELETED: False}})
    assert len(db_events) == 1
    assert isinstance(db_events[0], DbDeleteEvent)
    assert db_events[0].fqid == "a/1"


def test_translate_delete_fqid_not_existent(event_translator, request_events):
    event = RequestDeleteEvent("a/1")
    with pytest.raises(ModelDoesNotExist):
        event_translator.translate(event, {})


def test_translate_delete_fqid_already_deleted(event_translator, request_events):
    event = RequestDeleteEvent("a/1")
    with pytest.raises(ModelDoesNotExist):
        event_translator.translate(event, {"a/1": {META_DELETED: True}})


def test_translate_restore(event_translator, request_events):
    event = RequestRestoreEvent("a/1")
    db_events = event_translator.translate(event, {"a/1": {META_DELETED: True}})
    assert len(db_events) == 1
    assert isinstance(db_events[0], DbRestoreEvent)
    assert db_events[0].fqid == "a/1"


def test_translate_restore_fqid_not_existent(event_translator, request_events):
    event = RequestRestoreEvent("a/1")
    with pytest.raises(ModelNotDeleted):
        event_translator.translate(event, {})


def test_translate_delete_fqid_not_deleted(event_translator, request_events):
    event = RequestRestoreEvent("a/1")
    with pytest.raises(ModelNotDeleted):
        event_translator.translate(event, {"a/1": {META_DELETED: False}})


def test_translate_single_unknown_type(event_translator):
    with pytest.raises(BadCodingError):
        event_translator.translate(None, MagicMock())
