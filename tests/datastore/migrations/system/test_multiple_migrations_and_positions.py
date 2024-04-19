from openslides_backend.migrations import BaseEvent, BaseEventMigration, CreateEvent

from ..util import get_lambda_event_migration, get_noop_event_migration


def test_multiple_migrations_together(
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
):
    write(
        {"type": "create", "fqid": "a/1", "fields": {"f": 1, "g": 1, "h": [], "i": [1]}}
    )
    write(
        {
            "type": "update",
            "fqid": "a/1",
            "fields": {"f": None, "g": 2},
            "list_fields": {"add": {"h": [1]}, "remove": {"i": [1]}},
        }
    )
    write({"type": "delete", "fqid": "a/1"})
    write({"type": "restore", "fqid": "a/1"})
    set_migration_index_to_1()
    previous_model = read_model("a/1")

    migration_handler.register_migrations(
        get_noop_event_migration(2),
        get_noop_event_migration(3),
        get_noop_event_migration(4),
    )
    migration_handler.finalize()

    assert_model("a/1", previous_model)
    assert_finalized()


def test_second_position_access_old_and_new_data(
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "create", "fqid": "trigger/1", "fields": {}})
    set_migration_index_to_1()

    class TestMigration(BaseEventMigration):
        target_migration_index = 2

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> list[BaseEvent] | None:
            if event.fqid == "a/1":
                # explicitly modify the event instead of creating a new one
                event.data["f_new"] = event.data["f"]
                del event.data["f"]
                return [event]
            else:
                old = self.old_accessor.get_model("a/1")
                new = self.new_accessor.get_model("a/1")
                assert "f" in old
                assert "f_new" in new
                assert old["f"] == new["f_new"]
                return None

    migration_handler.register_migrations(TestMigration)
    migration_handler.finalize()
    assert_finalized()


def test_second_migration_gets_events_from_first(
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    first = get_lambda_event_migration(lambda _: [CreateEvent("a/2", {})])

    captured_event = (
        {}
    )  # use an object to transport the captured event out of the function scope

    def capture_handler(event):
        captured_event["event"] = event
        return [event]

    second = get_lambda_event_migration(capture_handler, target_migration_index=3)

    migration_handler.register_migrations(first, second)
    migration_handler.finalize()

    assert_finalized()
    assert "event" in captured_event
    assert captured_event["event"].fqid == "a/2"


def test_amount_events(
    migration_handler, write, set_migration_index_to_1, assert_count
):
    write(
        {"type": "create", "fqid": "a/1", "fields": {"f": 1, "g": 1, "h": [], "i": [1]}}
    )
    set_migration_index_to_1()

    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )
    migration_handler.finalize()

    assert_count("events", 1)
    assert_count("migration_events", 0)


def test_migrate_finalize(
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
):
    write(
        {"type": "create", "fqid": "a/1", "fields": {"f": 1, "g": 1, "h": [], "i": [1]}}
    )
    write(
        {
            "type": "update",
            "fqid": "a/1",
            "fields": {"f": None, "g": 2},
            "list_fields": {"add": {"h": [1]}, "remove": {"i": [1]}},
        }
    )
    write({"type": "delete", "fqid": "a/1"})
    write({"type": "restore", "fqid": "a/1"})
    set_migration_index_to_1()
    previous_model = read_model("a/1")

    migration_handler.register_migrations(
        get_noop_event_migration(2),
        get_noop_event_migration(3),
        get_noop_event_migration(4),
    )
    migration_handler.migrate()
    migration_handler.finalize()

    assert_model("a/1", previous_model)
    assert_finalized()


def test_multiple_migrations_following(
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
):
    write(
        {"type": "create", "fqid": "a/1", "fields": {"f": 1, "g": 1, "h": [], "i": [1]}}
    )
    write(
        {
            "type": "update",
            "fqid": "a/1",
            "fields": {"f": None, "g": 2},
            "list_fields": {"add": {"h": [1]}, "remove": {"i": [1]}},
        }
    )
    write({"type": "delete", "fqid": "a/1"})
    write({"type": "restore", "fqid": "a/1"})
    set_migration_index_to_1()
    previous_model = read_model("a/1")

    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )
    migration_handler.finalize()

    assert_model("a/1", previous_model)
    assert_finalized()

    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_event_migration(2),
        get_noop_event_migration(3),
        get_noop_event_migration(4),
        get_noop_event_migration(5),
    )
    migration_handler.finalize()

    assert_model("a/1", previous_model)
    assert_finalized()


def test_multiple_migrations_one_finalizing(
    migration_handler,
    write,
    set_migration_index_to_1,
    read_model,
    assert_model,
    assert_finalized,
):
    """This tests the deletion of the keyframe in move_to_next_position"""
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": 2}})
    set_migration_index_to_1()
    previous_model = read_model("a/1")

    migration_handler.register_migrations(get_noop_event_migration(2))
    migration_handler.migrate()
    migration_handler.migrations_by_target_migration_index = {}
    migration_handler.register_migrations(
        get_noop_event_migration(2), get_noop_event_migration(3)
    )
    migration_handler.finalize()

    assert_model("a/1", previous_model)
    assert_finalized()
