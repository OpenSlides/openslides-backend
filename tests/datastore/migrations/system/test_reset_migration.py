from openslides_backend.migrations import CreateEvent

from ..util import get_lambda_event_migration, get_noop_event_migration


def test_no_migrations(
    migration_handler, write, set_migration_index_to_1, assert_count
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    write({"type": "create", "fqid": "a/2", "fields": {}})
    set_migration_index_to_1()

    assert_count("migration_keyframes", 0)
    assert_count("migration_positions", 0)
    assert_count("migration_events", 0)

    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.reset()

    assert_count("migration_keyframes", 0)
    assert_count("migration_positions", 0)
    assert_count("migration_events", 0)


def test_ongoing_migrations(
    migration_handler, write, set_migration_index_to_1, assert_count
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    write({"type": "create", "fqid": "a/2", "fields": {}})
    set_migration_index_to_1()

    assert_count("migration_keyframes", 0)
    assert_count("migration_positions", 0)
    assert_count("migration_events", 0)

    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.migrate()

    assert_count("migration_keyframes", 2)
    assert_count("migration_positions", 2)
    assert_count("migration_events", 2)

    migration_handler.reset()

    assert_count("migration_keyframes", 0)
    assert_count("migration_positions", 0)
    assert_count("migration_events", 0)


def test_actual_migration(
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    query_single_value,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()
    previous_model = read_model("a/1")

    event = CreateEvent("a/2", {})
    migration_handler.register_migrations(get_lambda_event_migration(lambda _: [event]))
    migration_handler.migrate()
    migration_handler.reset()

    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.finalize()

    assert_model("a/1", previous_model)
    assert query_single_value("select min(migration_index) from positions") == 2
    assert query_single_value("select max(migration_index) from positions") == 2
