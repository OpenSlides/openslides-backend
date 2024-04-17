from unittest.mock import MagicMock

from ..util import get_noop_event_migration


def test_set_latest_migrate(
    migration_handler, connection_handler, write, query_single_value
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    write({"type": "create", "fqid": "a/2", "fields": {}})

    migration_handler.run_migrations = rm = MagicMock()
    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )
    migration_handler.migrate()

    rm.assert_not_called()
    assert query_single_value("select max(migration_index) from positions") == 3
    assert query_single_value("select min(migration_index) from positions") == 3


def test_migration_index_too_high_finalize(
    migration_handler, connection_handler, write, query_single_value
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    write({"type": "create", "fqid": "a/2", "fields": {}})

    migration_handler.run_migrations = rm = MagicMock()
    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )
    migration_handler.finalize()

    rm.assert_not_called()
    assert query_single_value("select max(migration_index) from positions") == 3
    assert query_single_value("select min(migration_index) from positions") == 3
