import pytest

from openslides_backend.migrations import MismatchingMigrationIndicesException

from ..util import LogMock, get_noop_event_migration


def test_no_migrations_to_apply(
    migration_handler,
    write,
    set_migration_index_to_1,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.logger.info = i = LogMock()
    migration_handler.finalize()

    i.assert_called()
    assert "Position 1 from MI 1 to MI 2 ..." in i.output

    i.reset_mock()
    migration_handler.migrate()

    i.assert_called()
    assert "No event migrations to apply." in i.output
    assert "No model migrations to apply." in i.output


def test_finalizing_needed(
    migration_handler,
    write,
    set_migration_index_to_1,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.logger.info = i = LogMock()
    migration_handler.migrate()

    i.assert_called()
    assert "Position 1 from MI 1 to MI 2 ..." in i.output
    assert "Done. Finalizing is still needed." in i.output

    i.reset_mock()
    migration_handler.migrate()

    i.assert_called()
    assert "No event migrations to apply, but finalizing is still needed." in [
        c[0][0] for c in i.call_args_list
    ]


def test_finalizing_not_needed(
    migration_handler,
    write,
    set_migration_index_to_1,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.finalize()

    migration_handler.logger.info = i = LogMock()
    migration_handler.finalize()

    i.assert_called()
    assert "No event migrations to apply." in i.output
    assert "No model migrations to apply." in i.output


def test_migration_index_not_initialized(
    write,
    migration_handler,
):
    pass


def test_raising_migration_index(
    migration_handler,
    write,
    connection_handler,
    set_migration_index_to_1,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    write({"type": "create", "fqid": "a/2", "fields": {}})
    set_migration_index_to_1()
    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.migrate()

    with connection_handler.get_connection_context():
        connection_handler.execute(
            "update migration_positions set migration_index=1 where position=1",
            [],
        )

    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )

    with pytest.raises(MismatchingMigrationIndicesException) as e:
        migration_handler.migrate()

    assert (
        str(e.value)
        == "Position 2 has a higher migration index as it's predecessor (position 1)"
    )
