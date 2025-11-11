from ..shared.exceptions import ActionException
from .core.base_migrations import BaseMigration
from .core.events import (
    BadEventException,
    BaseEvent,
    CreateEvent,
    DeleteEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)
from .core.exceptions import (
    MigrationException,
    MigrationSetupException,
    MismatchingMigrationIndicesException,
)
from .migration_manager import MigrationManager


def get_backend_migration_index() -> int:
    # migration_classes = MigrationWrapper.load_migrations()

    backend_migration_index = 1
    # for migration_class in migration_classes:
    #     backend_migration_index = max(
    #         backend_migration_index, migration_class().target_migration_index
    #     )
    return backend_migration_index


def get_datastore_migration_index() -> int:
    # TODO: Re-implement
    # read_db = injector.get(ReadDatabase)
    # with read_db.get_context():
    #     datastore_migration_index = read_db.get_current_migration_index()
    # return datastore_migration_index

    return 1


def assert_migration_index() -> None:
    # TODO: Re-implement
    # connection = injector.get(ConnectionHandler)
    # with connection.get_connection_context():
    #     if connection.query_single_value("select count(*) from positions", []) == 0:
    #         return  # Datastore is empty; nothing to check.

    # datastore_migration_index = get_datastore_migration_index()

    # if datastore_migration_index == -1:
    #     return  # Datastore is up-to-date; nothing to do.

    # backend_migration_index = get_backend_migration_index()

    # if backend_migration_index > datastore_migration_index:
    #     raise ActionException(
    #         f"Missing {backend_migration_index-datastore_migration_index} migrations to apply."
    #     )

    # if backend_migration_index < datastore_migration_index:
    #     raise ActionException(
    #         f"Migration indices do not match: Datastore has {datastore_migration_index} and the backend has {backend_migration_index}"
    #     )
    pass
