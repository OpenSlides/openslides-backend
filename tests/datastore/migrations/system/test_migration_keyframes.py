import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    MigrationKeyframeModelDeleted,
    MigrationKeyframeModelDoesNotExist,
    MigrationKeyframeModelNotDeleted,
)
from openslides_backend.shared.patterns import Position


class BaseTest:
    meta_position: Position

    def _write(self, write, *data):
        raise NotImplementedError()

    @pytest.fixture()
    def write_data(self, write, set_migration_index_to_1):
        def _write_data(*data):
            self._write(write, *data)
            set_migration_index_to_1()

        yield _write_data

    def test_get_model(self, migration_handler, write_data):
        write_data({"type": "create", "fqid": "a/1", "fields": {"f": 1}})

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    old = inner_self.old_accessor.get_model("a/1")
                    new = inner_self.new_accessor.get_model("a/1")
                    assert old == new
                    assert old == {
                        "f": 1,
                        "meta_deleted": False,
                        "meta_position": self.meta_position,
                    }
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_model_does_not_exist(self, migration_handler, write_data):
        write_data()

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    with pytest.raises(MigrationKeyframeModelDoesNotExist):
                        inner_self.old_accessor.get_model("a/1")
                    with pytest.raises(MigrationKeyframeModelDoesNotExist):
                        inner_self.new_accessor.get_model("a/1")
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_model_deleted(self, migration_handler, write_data):
        write_data(
            {"type": "create", "fqid": "a/1", "fields": {"f": 1}},
            {"type": "delete", "fqid": "a/1"},
        )

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    with pytest.raises(MigrationKeyframeModelDeleted):
                        inner_self.old_accessor.get_model("a/1")
                    with pytest.raises(MigrationKeyframeModelDeleted):
                        inner_self.new_accessor.get_model("a/1")
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_deleted_model(self, migration_handler, write_data):
        write_data(
            {"type": "create", "fqid": "a/1", "fields": {"f": 1}},
            {"type": "delete", "fqid": "a/1"},
        )

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    old = inner_self.old_accessor.get_deleted_model("a/1")
                    new = inner_self.new_accessor.get_deleted_model("a/1")
                    assert old == new
                    assert old == {
                        "f": 1,
                        "meta_deleted": True,
                        "meta_position": self.meta_position,
                    }
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_deleted_model_does_not_exists(self, migration_handler, write_data):
        write_data()

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    with pytest.raises(MigrationKeyframeModelDoesNotExist):
                        inner_self.old_accessor.get_deleted_model("a/1")
                    with pytest.raises(MigrationKeyframeModelDoesNotExist):
                        inner_self.new_accessor.get_deleted_model("a/1")
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_deleted_model_not_deleted(self, migration_handler, write_data):
        write_data({"type": "create", "fqid": "a/1", "fields": {"f": 1}})

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    with pytest.raises(MigrationKeyframeModelNotDeleted):
                        inner_self.old_accessor.get_deleted_model("a/1")
                    with pytest.raises(MigrationKeyframeModelNotDeleted):
                        inner_self.new_accessor.get_deleted_model("a/1")
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_model_ignore_deleted_is_deleted(self, migration_handler, write_data):
        write_data(
            {"type": "create", "fqid": "a/1", "fields": {"f": 1}},
            {"type": "delete", "fqid": "a/1"},
        )

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    old = inner_self.old_accessor.get_model_ignore_deleted("a/1")
                    new = inner_self.new_accessor.get_model_ignore_deleted("a/1")
                    assert old == new
                    assert old == (
                        {
                            "f": 1,
                            "meta_deleted": True,
                            "meta_position": self.meta_position,
                        },
                        True,
                    )
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_model_ignore_deleted_not_deleted(self, migration_handler, write_data):
        write_data({"type": "create", "fqid": "a/1", "fields": {"f": 1}})

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    old = inner_self.old_accessor.get_model_ignore_deleted("a/1")
                    new = inner_self.new_accessor.get_model_ignore_deleted("a/1")
                    assert old == new
                    assert old == (
                        {
                            "f": 1,
                            "meta_deleted": False,
                            "meta_position": self.meta_position,
                        },
                        False,
                    )
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_model_ignore_deleted_does_not_exist(
        self, migration_handler, write_data
    ):
        write_data()

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    with pytest.raises(MigrationKeyframeModelDoesNotExist):
                        inner_self.old_accessor.get_model_ignore_deleted("a/1")
                    with pytest.raises(MigrationKeyframeModelDoesNotExist):
                        inner_self.new_accessor.get_model_ignore_deleted("a/1")
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_model_exists(self, migration_handler, write_data):
        write_data({"type": "create", "fqid": "a/1", "fields": {"f": 1}})

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    assert inner_self.old_accessor.model_exists("a/1")
                    assert inner_self.new_accessor.model_exists("a/1")
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_model_exists_does_not_exist(self, migration_handler, write_data):
        write_data()

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    assert not inner_self.old_accessor.model_exists("a/1")
                    assert not inner_self.new_accessor.model_exists("a/1")
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_all_ids_for_collection(self, migration_handler, write_data):
        write_data(
            {"type": "create", "fqid": "a/1", "fields": {}},
            {"type": "create", "fqid": "a/1337", "fields": {}},
            {"type": "create", "fqid": "a/2", "fields": {}},
            {"type": "create", "fqid": "a/42", "fields": {}},
            {"type": "create", "fqid": "a/128", "fields": {}},
        )

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    old = inner_self.old_accessor.get_all_ids_for_collection("a")
                    new = inner_self.new_accessor.get_all_ids_for_collection("a")
                    assert old == new
                    assert old == {1, 1337, 2, 42, 128}
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_all_ids_for_collection_single_id(self, migration_handler, write_data):
        write_data({"type": "create", "fqid": "a/1", "fields": {}})

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    old = inner_self.old_accessor.get_all_ids_for_collection("a")
                    new = inner_self.new_accessor.get_all_ids_for_collection("a")
                    assert old == new
                    assert old == {1}
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()

    def test_get_all_ids_for_collection_empty_collection(
        self, migration_handler, write_data
    ):
        write_data()

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "trigger/1":
                    old = inner_self.old_accessor.get_all_ids_for_collection("a")
                    new = inner_self.new_accessor.get_all_ids_for_collection("a")
                    assert old == new
                    assert old == set()
                return None

        migration_handler.register_migrations(MyMigration)
        migration_handler.finalize()


class TestInitialMigrationKeyframeModifier(BaseTest):
    meta_position = 1

    def _write(self, write, *data):
        if data:
            write(*data)
        write({"type": "create", "fqid": "trigger/1", "fields": {}})


class TestDatabaseMigrationKeyframeModifier(BaseTest):
    meta_position = 2

    def _write(self, write, *data):
        write({"type": "create", "fqid": "dummy/1", "fields": {}})
        if data:
            write(*data)
        write({"type": "create", "fqid": "trigger/1", "fields": {}})


class TestSkippedPositionMigrationKeyframeModifier(BaseTest):
    meta_position = 3

    def _write(self, write, *data):
        write({"type": "create", "fqid": "dummy/1", "fields": {}})
        # manually skip position 2
        connection_handler = injector.get(ConnectionHandler)
        with connection_handler.get_connection_context():
            connection_handler.execute(
                "ALTER SEQUENCE positions_position_seq RESTART WITH 3", []
            )
        if data:
            write(*data)
        write({"type": "create", "fqid": "trigger/1", "fields": {"f": 1}})
