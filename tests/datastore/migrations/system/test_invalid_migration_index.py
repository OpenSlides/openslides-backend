from unittest.mock import MagicMock

import pytest

from openslides_backend.migrations import MismatchingMigrationIndicesException

from ..util import get_noop_event_migration


def test_migration_index_too_high_migrate(
    migration_handler, write, set_migration_index_to_1
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()
    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )
    migration_handler.migrate()

    migration_handler.run_migrations = rm = MagicMock()
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_event_migration(2)
    )  # One migration too few

    with pytest.raises(MismatchingMigrationIndicesException):
        migration_handler.migrate()

    rm.assert_not_called()


def test_migration_index_too_high_finalize(
    migration_handler, write, set_migration_index_to_1
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()
    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )
    migration_handler.finalize()

    migration_handler.run_migrations = rm = MagicMock()
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_event_migration(2)
    )  # One migration too few

    with pytest.raises(MismatchingMigrationIndicesException):
        migration_handler.finalize()

    rm.assert_not_called()


def test_migration_index_too_high_reset(
    migration_handler, write, set_migration_index_to_1
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()
    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )
    migration_handler.finalize()

    migration_handler._delete_migration_keyframes = dmk = MagicMock()
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_event_migration(2)
    )  # One migration too few

    with pytest.raises(MismatchingMigrationIndicesException):
        migration_handler.reset()

    dmk.assert_not_called()


def test_migration_index_inconsistent(migration_handler, write, connection_handler):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    write({"type": "create", "fqid": "a/2", "fields": {}})
    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.finalize()
    with connection_handler.get_connection_context():
        connection_handler.execute(
            "update positions set migration_index=1 where position=2", []
        )

    migration_handler.run_migrations = rm = MagicMock()
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )

    with pytest.raises(MismatchingMigrationIndicesException):
        migration_handler.migrate()

    rm.assert_not_called()
