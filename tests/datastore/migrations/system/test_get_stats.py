from openslides_backend.datastore.writer.core import RequestCreateEvent
from openslides_backend.migrations.core.events import CreateEvent
from openslides_backend.migrations.core.migration_handler import MigrationState

from ..util import LogMock, get_lambda_event_migration, get_lambda_model_migration


def test_get_stats(
    migration_handler, write, set_migration_index_to_1, assert_finalized, assert_model
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(
        get_lambda_event_migration(lambda e: [CreateEvent("a/1", {"f": 1})]),
        get_lambda_model_migration(lambda _: [RequestCreateEvent("a/2", {"f": 1})], 3),
    )
    migration_handler.logger.info = i = LogMock()
    assert migration_handler.get_stats() == {
        "status": MigrationState.MIGRATION_REQUIRED,
        "current_migration_index": 1,
        "target_migration_index": 3,
        "positions": 1,
        "events": 1,
        "partially_migrated_positions": 0,
        "fully_migrated_positions": 0,
    }
    i.assert_not_called()
