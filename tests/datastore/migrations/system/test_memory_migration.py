import pytest

from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    MismatchingMigrationIndicesException,
    setup,
)
from openslides_backend.migrations.core.base_migrations.base_model_migration import (
    BaseModelMigration,
)
from openslides_backend.migrations.core.events import CreateEvent
from openslides_backend.migrations.core.migration_handler import (
    MigrationHandlerImplementationMemory,
)
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.interfaces.write_request import RequestUpdateEvent
from openslides_backend.shared.patterns import META_DELETED
from tests.datastore.migrations.util import (
    get_lambda_event_migration,
    get_lambda_model_migration,
    get_noop_event_migration,
)


class TestInMemoryMigration:
    @pytest.fixture(autouse=True)
    def setup_memory_migration(reset_di):
        setup(memory_only=True)

    def test_simple_migration(
        self, migration_handler: MigrationHandlerImplementationMemory
    ):
        data = {"a/1": {"f": 1}}

        class MyMigration(BaseEventMigration):
            target_migration_index = 2

            def migrate_event(
                inner_self,
                event: BaseEvent,
            ) -> list[BaseEvent] | None:
                if event.fqid == "a/1":
                    event.data["f"] = 2
                return [event]

        migration_handler.register_migrations(MyMigration)
        migration_handler.set_import_data(data, 1)
        migration_handler.finalize()
        migrated_models = migration_handler.get_migrated_models()
        assert migrated_models == {"a/1": {"f": 2}}

    def test_mismatching_migration_index(
        self, migration_handler: MigrationHandlerImplementationMemory
    ):
        data = {"a/1": {"f": 1}}

        migration_handler.register_migrations(get_noop_event_migration(2))
        migration_handler.set_import_data(data, 3)
        with pytest.raises(MismatchingMigrationIndicesException):
            migration_handler.finalize()

    def test_model_migration(
        self, migration_handler: MigrationHandlerImplementationMemory
    ):
        data = {"a/1": {"f": 1}}

        migration_handler.register_migrations(
            get_lambda_model_migration(lambda _: [RequestUpdateEvent("a/1", {"f": 2})])
        )
        migration_handler.set_import_data(data, 1)
        migration_handler.finalize()
        migrated_models = migration_handler.get_migrated_models()
        assert migrated_models == {"a/1": {"f": 2}}

    def test_event_and_model_migration(
        self, migration_handler: MigrationHandlerImplementationMemory
    ):
        data = {"a/1": {"f": 1}}

        migration_handler.register_migrations(
            get_lambda_event_migration(lambda _: [CreateEvent("a/1", {"f": 2})]),
            get_lambda_model_migration(
                lambda _: [RequestUpdateEvent("a/1", {"f": 3})], 3
            ),
        )
        migration_handler.set_import_data(data, 1)
        migration_handler.finalize()
        migrated_models = migration_handler.get_migrated_models()
        assert migrated_models == {"a/1": {"f": 3}}

    def test_model_migration_with_data_access(
        self, migration_handler: MigrationHandlerImplementationMemory
    ):
        data = {"a/1": {"id": 1, "f": 1}}

        def migrate_models(self: BaseModelMigration):
            assert self.reader.get("a/1") == {"id": 1, "f": 1, META_DELETED: False}
            assert self.reader.get_all("a") == {
                1: {"id": 1, "f": 1, META_DELETED: False}
            }
            assert self.reader.exists("a", FilterOperator("f", "=", 1)) is True
            assert self.reader.min("a", FilterOperator("f2", "=", None), "f") == 1

        migration_handler.register_migrations(
            get_lambda_model_migration(migrate_models)
        )
        migration_handler.set_import_data(data, 1)
        migration_handler.finalize()
        migrated_models = migration_handler.get_migrated_models()
        assert migrated_models == {"a/1": {"id": 1, "f": 1}}
