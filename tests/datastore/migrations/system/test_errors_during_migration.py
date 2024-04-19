# E.g. 3 positions, raise exception during the 2. position. test resume.

import pytest

from openslides_backend.migrations import BaseEventMigration

from ..util import get_lambda_event_migration, get_noop_event_migration


def do_raise(exception):
    def fn(*args, **kwargs):
        raise exception

    return fn


class AbortException(Exception):
    pass


def fail_handler(event):
    if event.fqid == "a/2":
        raise AbortException()
    else:
        return [event]


def test_failing_migration(
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    set_migration_index_to_1()
    previous_model = read_model("a/1")

    fail_migration = get_lambda_event_migration(do_raise(AbortException()))
    migration_handler.register_migrations(fail_migration)

    with pytest.raises(AbortException):
        migration_handler.migrate()

    # change migration to a successfull noop
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(get_noop_event_migration(2))

    migration_handler.finalize()

    assert_model("a/1", previous_model)
    assert_finalized()


def test_failing_migration_multi_positions(
    connection_handler,
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
    assert_count,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "create", "fqid": "a/2", "fields": {"f": 1}})
    write({"type": "create", "fqid": "a/3", "fields": {"f": 1}})
    set_migration_index_to_1()
    previous_models = (read_model("a/1"), read_model("a/2"), read_model("a/3"))

    migration_handler.register_migrations(get_lambda_event_migration(fail_handler))

    with pytest.raises(AbortException):
        migration_handler.migrate()

    assert_count("migration_positions", 1)
    assert_count("migration_events", 1)

    # change migration to a successfull noop
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(get_noop_event_migration(2))

    migration_handler.migrate()
    assert_count("migration_positions", 3)
    assert_count("migration_events", 3)

    migration_handler.finalize()

    assert_model("a/1", previous_models[0])
    assert_model("a/2", previous_models[1])
    assert_model("a/3", previous_models[2])
    assert_finalized()


def test_failing_migration_multi_positions_new_migration_after_fail(
    connection_handler,
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
    assert_count,
    query_single_value,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "create", "fqid": "a/2", "fields": {"f": 1}})
    write({"type": "create", "fqid": "a/3", "fields": {"f": 1}})
    set_migration_index_to_1()
    previous_models = (read_model("a/1"), read_model("a/2"), read_model("a/3"))

    migration_handler.register_migrations(get_lambda_event_migration(fail_handler))

    with pytest.raises(AbortException):
        migration_handler.migrate()

    assert_count("migration_positions", 1)
    assert_count("migration_events", 1)

    # change migration to two successfull noops
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )  # Here, a new migration is added!

    migration_handler.migrate()
    assert_count("migration_positions", 3)
    assert_count("migration_events", 3)

    migration_handler.finalize()

    assert query_single_value("select max(migration_index) from positions") == 3
    assert query_single_value("select min(migration_index) from positions") == 3
    assert_model("a/1", previous_models[0])
    assert_model("a/2", previous_models[1])
    assert_model("a/3", previous_models[2])
    assert_finalized()


def test_use_basemigration(
    connection_handler,
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
    assert_count,
    query_single_value,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    set_migration_index_to_1()

    class MyBaseMigration(BaseEventMigration):
        target_migration_index = 2

    migration_handler.register_migrations(MyBaseMigration)

    with pytest.raises(NotImplementedError):
        migration_handler.migrate()
