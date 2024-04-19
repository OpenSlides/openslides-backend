from unittest.mock import MagicMock, patch

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.flask_frontend import InvalidRequest
from openslides_backend.datastore.shared.util import BadCodingError, InvalidFormat
from openslides_backend.datastore.writer.core import Writer
from openslides_backend.datastore.writer.flask_frontend.json_handlers import (
    ReserveIdsHandler,
    WriteHandler,
)
from tests.datastore import reset_di  # noqa


@pytest.fixture()
def writer(reset_di):  # noqa
    injector.register_as_singleton(Writer, MagicMock)
    yield injector.get(Writer)


@pytest.fixture()
def write_handler():
    yield WriteHandler()


@pytest.fixture()
def reserve_ids_handler():
    yield ReserveIdsHandler()


class TestWriteHandler:
    def test_wrong_schema(self, write_handler):
        with pytest.raises(InvalidRequest):
            write_handler.write(None)

    def test_correct_schema(self, write_handler, writer):
        writer.write = w = MagicMock()
        event = MagicMock()
        write_handler.create_event = MagicMock(return_value=event)

        with patch(
            "openslides_backend.datastore.writer.flask_frontend.json_handlers.WriteRequest"
        ) as wr:
            write_handler.write(
                {
                    "user_id": -2,
                    "information": [None, True],
                    "locked_fields": {"some_string": 1},
                    "events": [
                        {"type": "create", "fqid": "some_fqid", "fields": {}},
                        {"type": "update", "fqid": "some_fqid", "fields": {}},
                        {"type": "delete", "fqid": "some_fqid"},
                        {"type": "restore", "fqid": "some_fqid"},
                    ],
                    "migration_index": 3,
                }
            )
            wr.assert_called_once()
            args = wr.call_args.args
            assert args == (
                [event, event, event, event],
                [None, True],
                -2,
                {"some_string": 1},
                3,
            )

        w.assert_called_once()

    def test_parse_events_create_event_type(self, write_handler):
        event = {"type": "create", "fqid": "a/1", "fields": ["not_a_dict"]}
        with pytest.raises(InvalidRequest):
            write_handler.parse_events([event])

    def test_parse_events_create_event_field_type(self, write_handler):
        event = {"type": "create", "fqid": "a/1", "fields": {1: "key_is_not_a_string"}}
        with pytest.raises(InvalidFormat):
            write_handler.parse_events([event])

    def test_parse_events_update_event_type(self, write_handler):
        event = {"type": "update", "fqid": "a/1", "fields": ["not_a_dict"]}
        with pytest.raises(InvalidRequest):
            write_handler.parse_events([event])

    def test_parse_events_update_event_field_type(self, write_handler):
        event = {"type": "update", "fqid": "a/1", "fields": {1: "key_is_not_a_string"}}
        with pytest.raises(InvalidFormat):
            write_handler.parse_events([event])

    def test_create_create_event(self, write_handler):
        fqid = MagicMock()
        fields = MagicMock()
        event = {"type": "create", "fqid": fqid, "fields": fields}
        with patch(
            "openslides_backend.datastore.writer.flask_frontend.json_handlers.RequestCreateEvent"
        ) as rce:
            rce.return_value = request_event = MagicMock()
            assert write_handler.create_event(event) == request_event
            assert rce.call_args.args == (fqid, fields)

    def test_create_update_event(self, write_handler):
        fqid = MagicMock()
        fields = MagicMock()
        list_fields = MagicMock()
        event = {
            "type": "update",
            "fqid": fqid,
            "fields": fields,
            "list_fields": list_fields,
        }
        with patch(
            "openslides_backend.datastore.writer.flask_frontend.json_handlers.RequestUpdateEvent"
        ) as rue:
            rue.return_value = request_event = MagicMock()
            assert write_handler.create_event(event) == request_event
            assert rue.call_args.args == (fqid, fields, list_fields)

    def test_create_delete_event(self, write_handler):
        fqid = MagicMock()
        event = {"type": "delete", "fqid": fqid}
        with patch(
            "openslides_backend.datastore.writer.flask_frontend.json_handlers.RequestDeleteEvent"
        ) as rde:
            rde.return_value = request_event = MagicMock()
            assert write_handler.create_event(event) == request_event
            assert rde.call_args.args == (fqid,)

    def test_create_restore_event(self, write_handler):
        fqid = MagicMock()
        event = {"type": "restore", "fqid": fqid}
        with patch(
            "openslides_backend.datastore.writer.flask_frontend.json_handlers.RequestRestoreEvent"
        ) as rre:
            rre.return_value = request_event = MagicMock()
            assert write_handler.create_event(event) == request_event
            assert rre.call_args.args == (fqid,)

    def test_create_unknown_event(self, write_handler):
        event = {"type": "unknwon", "fqid": "a/1"}
        with pytest.raises(BadCodingError):
            write_handler.create_event(event)


class TestReserveIdsHandler:
    def test_wrong_schema(self, reserve_ids_handler):
        with pytest.raises(InvalidRequest):
            reserve_ids_handler.reserve_ids(None)

    def test_correct_schema(self, reserve_ids_handler, writer):
        writer.reserve_ids = gi = MagicMock()
        data = {"collection": "my_collection", "amount": -3}
        reserve_ids_handler.reserve_ids(data)
        gi.assert_called_once()
        assert gi.call_args.args == (
            "my_collection",
            -3,
        )
