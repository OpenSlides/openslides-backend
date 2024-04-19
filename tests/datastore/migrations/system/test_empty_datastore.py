from unittest.mock import MagicMock

from ..util import get_noop_event_migration


def test_empty_datastore_migrate(migration_handler, assert_count):
    migration_handler.run_migrations = mr = MagicMock()
    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.migrate()

    mr.assert_not_called()
    assert_count("positions", 0)
    assert_count("models", 0)
    assert_count("migration_positions", 0)
    assert_count("migration_keyframes", 0)


def test_empty_datastore_finalize(migration_handler, assert_count):
    migration_handler.run_migrations = mr = MagicMock()
    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.finalize()

    mr.assert_not_called()
    assert_count("positions", 0)
    assert_count("models", 0)
    assert_count("migration_positions", 0)
    assert_count("migration_keyframes", 0)


def test_empty_datastore_reset(migration_handler, assert_count):
    migration_handler.run_migrations = mr = MagicMock()
    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.reset()

    mr.assert_not_called()
    assert_count("positions", 0)
    assert_count("models", 0)
    assert_count("migration_positions", 0)
    assert_count("migration_keyframes", 0)
