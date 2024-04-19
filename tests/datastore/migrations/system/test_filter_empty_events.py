from openslides_backend.migrations.core.events import (
    BaseEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)

from ..util import get_lambda_event_migration


def test_filter_empty_update(
    migration_handler,
    write,
    set_migration_index_to_1,
    assert_count,
    assert_model,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": 2}})
    set_migration_index_to_1()

    def remove_f(event: BaseEvent):
        if isinstance(event, UpdateEvent):
            del event.data["f"]
        return [event]

    migration_handler.register_migrations(get_lambda_event_migration(remove_f))
    migration_handler.finalize()

    assert_count("events", 1)
    assert_model(
        "a/1",
        {
            "f": 1,
            "meta_deleted": False,
            "meta_position": 1,
        },
    )


def test_filter_empty_listupdate(
    migration_handler,
    write,
    set_migration_index_to_1,
    assert_count,
    assert_model,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
    write(
        {
            "type": "update",
            "fqid": "a/1",
            "list_fields": {"add": {"f": [2]}, "remove": {"f": [1]}},
        }
    )
    set_migration_index_to_1()

    def remove_f(event: BaseEvent):
        if isinstance(event, ListUpdateEvent):
            del event.add["f"]
            del event.remove["f"]
        return [event]

    migration_handler.register_migrations(get_lambda_event_migration(remove_f))
    migration_handler.finalize()

    assert_count("events", 1)
    assert_model(
        "a/1",
        {
            "f": [1],
            "meta_deleted": False,
            "meta_position": 1,
        },
    )


def test_filter_empty_deletefields(
    migration_handler,
    write,
    set_migration_index_to_1,
    assert_count,
    assert_model,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": None}})
    set_migration_index_to_1()

    def remove_f(event: BaseEvent):
        if isinstance(event, DeleteFieldsEvent):
            event.data.remove("f")
        return [event]

    migration_handler.register_migrations(get_lambda_event_migration(remove_f))
    migration_handler.finalize()

    assert_count("events", 1)
    assert_model(
        "a/1",
        {
            "f": [1],
            "meta_deleted": False,
            "meta_position": 1,
        },
    )


def test_filter_no_events(
    migration_handler,
    write,
    set_migration_index_to_1,
    assert_count,
    assert_model,
):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": 2}})
    set_migration_index_to_1()

    migration_handler.register_migrations(
        get_lambda_event_migration(lambda e: [] if isinstance(e, UpdateEvent) else None)
    )
    migration_handler.finalize()

    assert_count("events", 1)
    assert_model(
        "a/1",
        {
            "f": 1,
            "meta_deleted": False,
            "meta_position": 1,
        },
    )
