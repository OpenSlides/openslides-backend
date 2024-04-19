import pytest

from openslides_backend.migrations import (
    BadEventException,
    CreateEvent,
    DeleteEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    RestoreEvent,
    UpdateEvent,
)
from openslides_backend.migrations.core.events import to_event

from ..util import get_lambda_event_migration


def test_to_event_unknown_event():
    row = {"type": "unknown"}
    with pytest.raises(BadEventException):
        to_event(row)


class TestCreateNewEvent:
    @pytest.fixture()
    def execute(self, migration_handler, write, set_migration_index_to_1):
        def _execute(event_fn, match):
            write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
            set_migration_index_to_1()

            migration_handler.register_migrations(
                get_lambda_event_migration(lambda _: [event_fn()])
            )
            with pytest.raises(BadEventException, match=match):
                migration_handler.migrate()

        yield _execute

    def test_fqid(self, execute):
        execute(lambda: CreateEvent("xyz", {}), match="xyz")

    def test_meta_fields(self, execute):
        execute(
            lambda: CreateEvent("a/1", {"meta_something": 1}),
            match="meta_something",
        )

    def test_not_a_field(self, execute):
        execute(
            lambda: CreateEvent("a/1", {"not_%_a_field": 1}),
            match="not_%_a_field",
        )

    def test_empty_field(self, execute):
        execute(lambda: CreateEvent("a/1", {"empty": None}), match="empty")

    def test_double_create(self, write, execute):
        write(
            {"type": "create", "fqid": "a/2", "fields": {"f": 1}}
        )  # this will be overwritten, too
        execute(
            lambda: CreateEvent("a/1", {"f": 1}),
            match="Model a/1 already exists",
        )


class TestUpdate:
    @pytest.fixture()
    def execute(self, migration_handler, write, set_migration_index_to_1):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        write({"type": "update", "fqid": "a/1", "fields": {"f": 2}})
        set_migration_index_to_1()

        def _execute(event_fn, match):
            migration_handler.register_migrations(
                get_lambda_event_migration(
                    lambda e: [event_fn()] if e.type == "update" else [e]
                )
            )
            with pytest.raises(BadEventException, match=match):
                migration_handler.migrate()

        yield _execute

    def test_fqid(self, execute):
        execute(lambda: UpdateEvent("xyz", {}), match="xyz")

    def test_meta_fields(self, execute):
        execute(
            lambda: UpdateEvent("a/1", {"meta_something": 1}),
            match="meta_something",
        )

    def test_not_a_field(self, execute):
        execute(
            lambda: UpdateEvent("a/1", {"not_%_a_field": 1}),
            match="not_%_a_field",
        )

    def test_empty_field(self, execute):
        execute(lambda: UpdateEvent("a/1", {"empty": None}), match="empty")

    def test_update_without_create(
        self, migration_handler, write, set_migration_index_to_1
    ):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(lambda _: [UpdateEvent("a/1", {"f": 2})])
        )
        with pytest.raises(BadEventException, match="Model a/1 does not exist"):
            migration_handler.migrate()

    def test_update_after_delete(
        self, migration_handler, write, set_migration_index_to_1
    ):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        write({"type": "delete", "fqid": "a/1"})
        write(
            {"type": "create", "fqid": "a/2", "fields": {"f": 1}}
        )  # this will be overwritten
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(
                lambda e: [UpdateEvent("a/1", {"f": 2})] if e.fqid == "a/2" else [e]
            )
        )
        with pytest.raises(BadEventException, match="Model a/1 is deleted"):
            migration_handler.migrate()


class TestDeleteFields:
    @pytest.fixture()
    def execute(self, migration_handler, write, set_migration_index_to_1):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        write(
            {"type": "update", "fqid": "a/1", "fields": {"f": None}}
        )  # will be converted to a deletefields event
        set_migration_index_to_1()

        def _execute(event_fn, match):
            migration_handler.register_migrations(
                get_lambda_event_migration(
                    lambda e: [event_fn()] if e.type == "deletefields" else [e]
                )
            )
            with pytest.raises(BadEventException, match=match):
                migration_handler.migrate()

        yield _execute

    def test_fqid(self, execute):
        execute(lambda: DeleteFieldsEvent("xyz", []), "xyz")

    def test_meta_fields(self, execute):
        execute(
            lambda: DeleteFieldsEvent("a/1", ["meta_something"]),
            "meta_something",
        )

    def test_not_a_field(self, execute):
        execute(
            lambda: DeleteFieldsEvent("a/1", ["not_%_a_field"]),
            "not_%_a_field",
        )

    def test_deletefields_without_create(
        self, migration_handler, write, set_migration_index_to_1
    ):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(lambda _: [DeleteFieldsEvent("a/1", ["f"])])
        )
        with pytest.raises(BadEventException, match="Model a/1 does not exist"):
            migration_handler.migrate()

    def test_deletefields_after_delete(
        self, migration_handler, write, set_migration_index_to_1
    ):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        write({"type": "delete", "fqid": "a/1"})
        write(
            {"type": "create", "fqid": "a/2", "fields": {"f": 1}}
        )  # this will be overwritten
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(
                lambda e: [DeleteFieldsEvent("a/1", ["f"])] if e.fqid == "a/2" else [e]
            )
        )
        with pytest.raises(BadEventException, match="Model a/1 is deleted"):
            migration_handler.migrate()


class TestListUpdate:
    @pytest.fixture()
    def execute(self, migration_handler, write, set_migration_index_to_1):
        write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
        write(
            {"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [2]}}}
        )  # will be converted to a listfields event
        set_migration_index_to_1()

        def _execute(event_fn, match):
            migration_handler.register_migrations(
                get_lambda_event_migration(
                    lambda e: [event_fn()] if e.type == "listfields" else [e]
                )
            )
            with pytest.raises(BadEventException, match=match):
                migration_handler.migrate()

        yield _execute

    def test_fqid(self, execute):
        execute(lambda: ListUpdateEvent("xyz", {"add": {"f": [1]}}), "xyz")

    def test_meta_fields(self, execute):
        execute(
            lambda: ListUpdateEvent("a/1", {"add": {"meta_something": [2]}}),
            "meta_something",
        )

    def test_not_a_field(self, execute):
        execute(
            lambda: ListUpdateEvent("a/1", {"add": {"not_%_a_field": [2]}}),
            "not_%_a_field",
        )

    def test_additional_key(self, execute):
        execute(
            lambda: ListUpdateEvent("a/1", {"add": {"f": [2]}, "unknown": {"f": [2]}}),
            "Only add and remove is allowed",
        )

    def test_listfields_without_create(
        self, migration_handler, write, set_migration_index_to_1
    ):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(
                lambda _: [ListUpdateEvent("a/1", {"add": {"f": [2]}})]
            )
        )
        with pytest.raises(BadEventException, match="Model a/1 does not exist"):
            migration_handler.migrate()

    def test_listfields_after_delete(
        self, migration_handler, write, set_migration_index_to_1
    ):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        write({"type": "delete", "fqid": "a/1"})
        write(
            {"type": "create", "fqid": "a/2", "fields": {"f": 1}}
        )  # this will be overwritten
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(
                lambda e: (
                    [ListUpdateEvent("a/1", {"add": {"f": [2]}})]
                    if e.fqid == "a/2"
                    else [e]
                )
            )
        )
        with pytest.raises(BadEventException, match="Model a/1 is deleted"):
            migration_handler.migrate()


class TestListUpdateModify:
    @pytest.fixture()
    def execute(self, migration_handler, write, set_migration_index_to_1):
        write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
        write(
            {"type": "update", "fqid": "a/1", "list_fields": {"add": {"f": [2]}}}
        )  # will be converted to a listfields event
        set_migration_index_to_1()

        def _execute(event_fn, match):
            migration_handler.register_migrations(
                get_lambda_event_migration(
                    lambda e: [event_fn(e)] if e.type == "listfields" else [e]
                )
            )
            with pytest.raises(BadEventException, match=match):
                migration_handler.migrate()

        yield _execute

    def test_fqid(self, execute):
        def handle(event):
            event.fqid = "xyz"
            return event

        execute(handle, match="xyz")

    def test_meta_fields(self, execute):
        def handle(event):
            event.add = {"meta_something": [2]}
            return event

        execute(handle, "meta_something")

    def test_not_a_field(self, execute):
        def handle(event):
            event.add = {"not_%_a_field": [2]}
            return event

        execute(handle, "not_%_a_field")


class TestDelete:
    def test_fqid(self, migration_handler, write, set_migration_index_to_1):
        write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
        write({"type": "delete", "fqid": "a/1"})
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(
                lambda e: [DeleteEvent("xyz")] if e.type == "delete" else [e]
            )
        )
        with pytest.raises(BadEventException, match="xyz"):
            migration_handler.migrate()

    def test_delete_without_create(
        self, migration_handler, write, set_migration_index_to_1
    ):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(lambda _: [DeleteEvent("a/1")])
        )
        with pytest.raises(BadEventException, match="Model a/1 does not exist"):
            migration_handler.migrate()

    def test_double_delete(self, migration_handler, write, set_migration_index_to_1):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        write({"type": "create", "fqid": "a/2", "fields": {"f": 1}})
        write({"type": "update", "fqid": "a/2", "fields": {"f": 1}})
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(
                lambda e: [DeleteEvent("a/1")] if e.fqid == "a/2" else [e]
            )
        )
        with pytest.raises(BadEventException, match="Model a/1 is deleted"):
            migration_handler.migrate()


class TestRestore:
    def test_fqid(self, migration_handler, write, set_migration_index_to_1):
        write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
        write({"type": "delete", "fqid": "a/1"})
        write({"type": "restore", "fqid": "a/1"})
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(
                lambda e: [RestoreEvent("xyz")] if e.type == "restore" else [e]
            )
        )
        with pytest.raises(BadEventException, match="xyz"):
            migration_handler.migrate()

    def test_restore_without_create(
        self, migration_handler, write, set_migration_index_to_1
    ):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(lambda _: [RestoreEvent("a/1")])
        )
        with pytest.raises(BadEventException, match="Model a/1 does not exist"):
            migration_handler.migrate()

    def test_restore_without_delete(
        self, migration_handler, write, set_migration_index_to_1
    ):
        write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
        write({"type": "create", "fqid": "a/2", "fields": {"f": 1}})
        set_migration_index_to_1()
        migration_handler.register_migrations(
            get_lambda_event_migration(
                lambda e: [RestoreEvent("a/1")] if e.fqid == "a/2" else [e]
            )
        )
        with pytest.raises(BadEventException, match="Model a/1 is not deleted"):
            migration_handler.migrate()
