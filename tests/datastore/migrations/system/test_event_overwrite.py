from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    CreateEvent,
    UpdateEvent,
)

from ..util import get_lambda_event_migration, get_noop_event_migration


def test_returning_original_events(
    migration_handler, connection_handler, write, set_migration_index_to_1
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    set_migration_index_to_1()

    with connection_handler.get_connection_context():
        original_events = connection_handler.query(
            "select * from events order by id", []
        )

    migration_handler.register_migrations(get_lambda_event_migration(lambda e: [e]))
    migration_handler.finalize()

    with connection_handler.get_connection_context():
        new_events = connection_handler.query("select * from events order by id", [])
    assert new_events == original_events


def test_new_events(
    migration_handler,
    connection_handler,
    write,
    set_migration_index_to_1,
    assert_count,
    assert_model,
    exists_model,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    new_events = [CreateEvent(f"a/{i}", {}) for i in (2, 3, 4)]
    migration_handler.register_migrations(
        get_lambda_event_migration(lambda e: new_events)
    )
    migration_handler.finalize()

    assert_count("events", 3)
    assert not exists_model("a/1")
    expected_model = {"meta_deleted": False, "meta_position": 1}
    assert_model("a/2", expected_model)
    assert_model("a/3", expected_model)
    assert_model("a/4", expected_model)


def test_new_events_multiple_positions(
    migration_handler,
    connection_handler,
    write,
    set_migration_index_to_1,
    assert_count,
    assert_model,
    exists_model,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    write({"type": "create", "fqid": "b/1", "fields": {}})
    set_migration_index_to_1()

    a_new_events = [CreateEvent(f"a/{i}", {}) for i in (2, 3)]
    b_new_events = [CreateEvent(f"b/{i}", {}) for i in (2, 3)]
    migration_handler.register_migrations(
        get_lambda_event_migration(
            lambda e: a_new_events if e.fqid == "a/1" else b_new_events
        )
    )
    migration_handler.finalize()

    assert_count("events", 4)
    assert not exists_model("a/1")
    assert not exists_model("b/1")
    assert_model("a/2", {"meta_deleted": False, "meta_position": 1})
    assert_model("a/3", {"meta_deleted": False, "meta_position": 1})
    assert_model("b/2", {"meta_deleted": False, "meta_position": 2})
    assert_model("b/3", {"meta_deleted": False, "meta_position": 2})


def test_new_events_rebuilding_order(
    migration_handler,
    connection_handler,
    write,
    set_migration_index_to_1,
    assert_model,
    exists_model,
    assert_count,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": 2}})
    set_migration_index_to_1()

    create_new_events = [
        CreateEvent("a/1", {"f": 4}),
        UpdateEvent("a/1", {"f": 3}),
    ]
    update_new_events = [
        UpdateEvent("a/1", {"f": 2}),
        UpdateEvent("a/1", {"f": 1}),
    ]
    migration_handler.register_migrations(
        get_lambda_event_migration(
            lambda e: create_new_events if e.type == "create" else update_new_events
        )
    )
    migration_handler.finalize()

    assert_count("events", 4)

    expected = {"meta_deleted": False, "meta_position": 2, "f": 1}
    assert_model("a/1", expected)
    read_db = injector.get(ReadDatabase)
    with connection_handler.get_connection_context():
        built_model = read_db.build_model_ignore_deleted("a/1")
    assert built_model == expected


def test_less_events(
    migration_handler,
    assert_count,
    write,
    set_migration_index_to_1,
    assert_model,
    exists_model,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": None, "f2": 2}})
    set_migration_index_to_1()
    assert_count("events", 3)

    migration_handler.register_migrations(
        get_noop_event_migration(2),
        get_lambda_event_migration(
            lambda e: (
                [e] if isinstance(e, CreateEvent) or isinstance(e, UpdateEvent) else []
            ),
            target_migration_index=3,
        ),
    )
    migration_handler.finalize()

    assert_count("events", 2)
    assert_model("a/1", {"f": 1, "f2": 2, "meta_deleted": False, "meta_position": 2})


def test_return_none_with_modifications(
    migration_handler,
    assert_count,
    write,
    set_migration_index_to_1,
    assert_model,
    read_model,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    set_migration_index_to_1()
    previous_model = read_model("a/1")

    def handler(event):
        event.data["f2"] = "Hi"
        return None

    migration_handler.register_migrations(get_lambda_event_migration(handler))
    migration_handler.finalize()

    assert_model("a/1", previous_model)


def test_additional_events(
    migration_handler,
    connection_handler,
    assert_count,
    write,
    set_migration_index_to_1,
    assert_model,
    exists_model,
):
    write({"type": "create", "fqid": "a/1", "fields": {}})
    set_migration_index_to_1()

    class TestMigration(BaseEventMigration):
        target_migration_index = 2

        def migrate_event(
            self,
            event: BaseEvent,
        ) -> list[BaseEvent] | None:
            return None

        def get_additional_events(self) -> list[BaseEvent] | None:
            """
            Here, additional events can be returned that are appended to the position after
            the migrated events. Return None if there are no such additional events. This is
            also the default behavior.
            """
            return [CreateEvent(f"a/{i}", {}) for i in (2, 3, 4)]

    migration_handler.register_migrations(TestMigration)
    migration_handler.finalize()

    assert_count("events", 4)
    for i in range(4):
        assert_model(f"a/{i+1}", {"meta_deleted": False, "meta_position": 1})
