import copy
from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.flask_frontend import InvalidRequest
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.shared.util import InvalidFormat
from openslides_backend.datastore.writer.core import Database
from openslides_backend.datastore.writer.core import setup_di as core_setup_di
from openslides_backend.datastore.writer.flask_frontend.json_handlers import (
    WriteHandler,
)
from openslides_backend.shared.patterns import META_FIELD_PREFIX
from tests.datastore import reset_di  # noqa


@pytest.fixture(autouse=True)
def setup_di(reset_di):  # noqa
    injector.register_as_singleton(Database, MagicMock)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    core_setup_di()


@pytest.fixture()
def write_handler():
    yield WriteHandler()


@pytest.fixture()
def valid_metadata():
    yield copy.deepcopy(
        {"user_id": 1, "information": {}, "locked_fields": {}, "events": []}
    )


@pytest.fixture()
def create_event():
    return copy.deepcopy({"type": "create", "fqid": "a/1", "fields": {"f": 1}})


def test_no_dict(write_handler):
    with pytest.raises(InvalidRequest):
        write_handler.write([True, "??"])


def test_no_events(write_handler, valid_metadata):
    with pytest.raises(InvalidFormat):
        write_handler.write(valid_metadata)


def test_locked_fields_wrong_position(write_handler, valid_metadata, create_event):
    valid_metadata["locked_fields"]["a/1"] = -3
    valid_metadata["events"].append(create_event)

    with pytest.raises(InvalidFormat) as e:
        write_handler.write(valid_metadata)

    assert "a/1" in e.value.msg


def test_locked_fields_wrong_key(write_handler, valid_metadata, create_event):
    valid_metadata["locked_fields"]["invalid"] = 3
    valid_metadata["events"].append(create_event)

    with pytest.raises(InvalidFormat) as e:
        write_handler.write(valid_metadata)

    assert "invalid" in e.value.msg


class BaseTestCreateUpdateEvent:
    type: str

    def test_no_fqid(self, write_handler, valid_metadata):
        valid_metadata["events"].append({"type": self.type})

        with pytest.raises(InvalidRequest):
            write_handler.write(valid_metadata)

    def test_invalid_fqid(self, write_handler, valid_metadata):
        valid_metadata["events"].append(
            {
                "type": self.type,
                "fqid": "no_valid_fqid",
                "fields": {"f": 1, "none": None},
            }
        )

        with pytest.raises(InvalidFormat):
            write_handler.write(valid_metadata)

    def test_no_fields(self, write_handler, valid_metadata):
        valid_metadata["events"].append({"type": self.type, "fqid": "a/1"})

        with pytest.raises(InvalidRequest):
            write_handler.write(valid_metadata)

    def test_fields_not_string(self, write_handler, valid_metadata):
        valid_metadata["events"].append(
            {"type": self.type, "fqid": "a/1", "fields": {2: 2, "none": None}}
        )

        with pytest.raises(InvalidFormat):
            write_handler.write(valid_metadata)

    def test_fields_invalid_field_name(self, write_handler, valid_metadata):
        valid_metadata["events"].append(
            {
                "type": self.type,
                "fqid": "a/1",
                "fields": {"_not_allowed": 2, "none": None},
            }
        )

        with pytest.raises(InvalidFormat):
            write_handler.write(valid_metadata)

    def test_fields_invalid_meta_field(self, write_handler, valid_metadata):
        valid_metadata["events"].append(
            {"type": self.type, "fqid": "a/1", "fields": {META_FIELD_PREFIX: 2}}
        )

        with pytest.raises(InvalidFormat):
            write_handler.write(valid_metadata)


class TestCreateEvent(BaseTestCreateUpdateEvent):
    type = "create"


class TestUpdateEvent(BaseTestCreateUpdateEvent):
    type = "update"


def test_update_empty_fields(write_handler, valid_metadata):
    valid_metadata["events"].append({"type": "update", "fqid": "a/1", "fields": {}})

    with pytest.raises(InvalidRequest):
        write_handler.write(valid_metadata)


class BaseTestDeleteRestoreEvent:
    type: str

    def test_no_fqid(self, write_handler, valid_metadata):
        valid_metadata["events"].append({"type": self.type})

        with pytest.raises(InvalidRequest):
            write_handler.write(valid_metadata)

    def test_invalid_fqid(self, write_handler, valid_metadata):
        valid_metadata["events"].append({"type": self.type, "fqid": "no_valid_fqid"})

        with pytest.raises(InvalidFormat):
            write_handler.write(valid_metadata)


class TestDeleteEvent(BaseTestDeleteRestoreEvent):
    type = "delete"


class TestRestoreEvent(BaseTestDeleteRestoreEvent):
    type = "restore"
