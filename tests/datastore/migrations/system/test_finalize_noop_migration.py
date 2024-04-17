import pytest

from ..util import get_noop_event_migration


class Base:
    def write_data(self, write, *data):
        raise NotImplementedError()

    @pytest.fixture()
    def readback(
        self,
        migration_handler,
        write,
        set_migration_index_to_1,
        read_model,
        assert_model,
        query_single_value,
        assert_finalized,
    ):
        def _readback(*data):
            self.write_data(write, *data)
            set_migration_index_to_1()
            previous_model = read_model("a/1")

            migration_handler.register_migrations(get_noop_event_migration(2))
            migration_handler.finalize()

            assert_model("a/1", previous_model)
            assert query_single_value("select max(migration_index) from positions") == 2
            assert query_single_value("select min(migration_index) from positions") == 2
            assert_finalized()

        yield _readback

    def test_create(self, readback):
        readback({"type": "create", "fqid": "a/1", "fields": {"f": 1}})

    def test_update(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {"f": 1}},
            {"type": "update", "fqid": "a/1", "fields": {"f": 2}},
        )

    def test_deletefields(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {"f": 1}},
            {"type": "update", "fqid": "a/1", "fields": {"f": None}},
        )

    def test_listupdate_add(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {"f": [1]}},
            {"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [2]}}},
        )

    def test_listupdate_add_field_does_not_exist(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {}},
            {"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [1]}}},
        )

    def test_listupdate_add_double(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {"f": [1]}},
            {"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [1]}}},
        )

    def test_listupdate_remove(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {"f": [1]}},
            {"type": "update", "fqid": "a/1", "list_fields": {"remove": {"f": [1]}}},
        )

    def test_listupdate_remove_field_does_not_exist(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {}},
            {"type": "update", "fqid": "a/1", "list_fields": {"remove": {"f": [1]}}},
        )

    def test_listupdate_remove_empty(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {"f": []}},
            {"type": "update", "fqid": "a/1", "list_fields": {"remove": {"f": [1]}}},
        )

    def test_delete(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {}},
            {"type": "delete", "fqid": "a/1"},
        )

    def test_restore(self, readback):
        readback(
            {"type": "create", "fqid": "a/1", "fields": {}},
            {"type": "delete", "fqid": "a/1"},
            {"type": "restore", "fqid": "a/1"},
        )

    def test_id_sequence(
        self, migration_handler, write, query_single_value, assert_finalized
    ):
        migration_handler.register_migrations(get_noop_event_migration(2))
        self.write_data(
            write,
            {"type": "create", "fqid": "a/1", "fields": {"f": 1}},
            {"type": "create", "fqid": "a/3", "fields": {}},
            {"type": "create", "fqid": "b/5", "fields": {}},
        )
        migration_handler.finalize()

        assert (
            query_single_value("select id from id_sequences where collection=%s", ["a"])
            == 4
        )
        assert (
            query_single_value("select id from id_sequences where collection=%s", ["b"])
            == 6
        )
        assert_finalized()


class TestSinglePosition(Base):
    def write_data(self, write, *data):
        write(*data)


class TestMultiPositions(Base):
    def write_data(self, write, *data):
        for _data in data:
            write(_data)
