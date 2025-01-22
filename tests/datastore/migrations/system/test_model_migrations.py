from openslides_backend.datastore.writer.core.write_request import RequestUpdateEvent
from openslides_backend.migrations.core.base_migrations.base_model_migration import (
    BaseModelMigration,
)
from openslides_backend.migrations.core.events import CreateEvent
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.interfaces.write_request import RequestCreateEvent
from openslides_backend.shared.patterns import META_DELETED, META_POSITION
from tests.datastore.migrations.util import (
    LogMock,
    get_lambda_event_migration,
    get_lambda_model_migration,
)


def test_model_migration(
    migration_handler, write, set_migration_index_to_1, assert_finalized, assert_model
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(
        get_lambda_model_migration(lambda _: [RequestCreateEvent("a/2", {"f": 1})])
    )
    migration_handler.logger.info = i = LogMock()
    migration_handler.migrate()

    assert i.output == (
        "Running migrations.",
        "No event migrations to apply.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Done. Finalizing is still needed.",
    )

    i.reset_mock()
    migration_handler.finalize()

    assert i.output == (
        "Finalize migrations.",
        "No event migrations to apply.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Migrating models from MI 1 to MI 2 ...",
        "Cleaning collectionfield helper tables...",
        "Set the new migration index to 2...",
        "Done.",
    )
    assert_finalized(2)
    assert_model("a/2", {"f": 1, "meta_deleted": False, "meta_position": 2}, position=2)


def test_model_migration_with_database_access(
    migration_handler, write, set_migration_index_to_1, assert_finalized
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    set_migration_index_to_1()

    def migrate_models(self: BaseModelMigration):
        assert self.reader.get("a/1", ["f"]) == {"f": 1}
        assert self.reader.get_all("a", ["f"]) == {1: {"f": 1}}
        assert self.reader.exists("a", FilterOperator("f", "=", 1)) is True
        assert self.reader.min("a", FilterOperator("f2", "=", None), "f") == 1

    migration_handler.register_migrations(get_lambda_model_migration(migrate_models))
    migration_handler.finalize()
    assert_finalized(2)


def test_model_migration_no_events(
    migration_handler, write, set_migration_index_to_1, assert_finalized
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(get_lambda_model_migration(lambda _: None))
    migration_handler.logger.info = i = LogMock()
    migration_handler.finalize()

    assert i.output == (
        "Finalize migrations.",
        "No event migrations to apply.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Migrating models from MI 1 to MI 2 ...",
        "Cleaning collectionfield helper tables...",
        "Set the new migration index to 2...",
        "Done.",
    )
    assert_finalized(2)


def test_model_migration_after_event_migration(
    migration_handler, write, set_migration_index_to_1, assert_finalized, assert_model
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(
        get_lambda_event_migration(lambda _: [CreateEvent("a/1", {"f": 1})]),
        get_lambda_model_migration(lambda _: [RequestCreateEvent("a/2", {"f": 1})], 3),
    )
    migration_handler.logger.info = i = LogMock()
    migration_handler.migrate()

    assert i.output == (
        "Running migrations.",
        "1 event migration to apply.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Position 1 from MI 1 to MI 2 ...",
        "Done. Finalizing is still needed.",
    )

    i.reset_mock()
    migration_handler.finalize()

    assert i.output == (
        "Finalize migrations.",
        "No event migrations to apply, but finalizing is still needed.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Cleaning collectionfield helper tables...",
        "Calculate helper tables...",
        "Deleting all migration keyframes...",
        "Swap events and migration_events tables...",
        "Set the new migration index to 2...",
        "Clean up migration data...",
        "Migrating models from MI 2 to MI 3 ...",
        "Cleaning collectionfield helper tables...",
        "Set the new migration index to 3...",
        "Done.",
    )

    assert_finalized(3)
    assert_model("a/1", {"f": 1, "meta_deleted": False, "meta_position": 1}, position=2)
    assert_model("a/2", {"f": 1, "meta_deleted": False, "meta_position": 2}, position=2)


def test_model_migration_after_event_migration_finalize(
    migration_handler, write, set_migration_index_to_1, assert_finalized, assert_model
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(
        get_lambda_event_migration(lambda _: [CreateEvent("a/1", {"f": 1})]),
        get_lambda_model_migration(lambda _: [RequestCreateEvent("a/2", {"f": 1})], 3),
    )
    migration_handler.logger.info = i = LogMock()
    migration_handler.finalize()

    assert i.output == (
        "Finalize migrations.",
        "1 event migration to apply.",
        "1 model migration to apply.",
        "Current migration index: 1",
        "Position 1 from MI 1 to MI 2 ...",
        "Cleaning collectionfield helper tables...",
        "Calculate helper tables...",
        "Deleting all migration keyframes...",
        "Swap events and migration_events tables...",
        "Set the new migration index to 2...",
        "Clean up migration data...",
        "Migrating models from MI 2 to MI 3 ...",
        "Cleaning collectionfield helper tables...",
        "Set the new migration index to 3...",
        "Done.",
    )

    assert_finalized(3)
    assert_model("a/1", {"f": 1, "meta_deleted": False, "meta_position": 1}, position=2)
    assert_model("a/2", {"f": 1, "meta_deleted": False, "meta_position": 2}, position=2)


def test_multiple_model_migrations(
    migration_handler, write, set_migration_index_to_1, assert_finalized, assert_model
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    set_migration_index_to_1()
    final1 = {"g": [2, 3, 4, 5], META_POSITION: 4, META_DELETED: False}
    final2 = {"f": 1, META_POSITION: 2, META_DELETED: False}

    def migrate_models(self: BaseModelMigration):
        assert self.reader.get("a/1") == final1
        assert self.reader.get("a/2") == final2

    migration_handler.register_migrations(
        get_lambda_model_migration(lambda _: [RequestCreateEvent("a/2", {"f": 1})]),
        get_lambda_model_migration(
            lambda _: [RequestUpdateEvent("a/1", {"f": None, "g": [2, 3]})], 3
        ),
        get_lambda_model_migration(
            lambda _: [RequestUpdateEvent("a/1", {}, {"add": {"g": [4, 5]}})], 4
        ),
        get_lambda_model_migration(migrate_models, 5),
    )
    migration_handler.logger.info = i = LogMock()
    migration_handler.finalize()

    assert i.output == (
        "Finalize migrations.",
        "No event migrations to apply.",
        "4 model migrations to apply.",
        "Current migration index: 1",
        "Migrating models from MI 1 to MI 5 ...",
        "Cleaning collectionfield helper tables...",
        "Set the new migration index to 5...",
        "Done.",
    )

    assert_finalized(5)
    assert_model("a/1", {"f": 1, META_DELETED: False, META_POSITION: 1}, position=1)
    assert_model("a/1", {"f": 1, META_DELETED: False, META_POSITION: 1}, position=2)
    assert_model(
        "a/1", {"g": [2, 3], META_DELETED: False, META_POSITION: 3}, position=3
    )
    assert_model("a/1", final1, position=4)
    assert_model("a/2", final2, position=4)
