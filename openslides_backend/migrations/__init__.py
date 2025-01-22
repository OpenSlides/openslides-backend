from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import ReadDatabase

from ..shared.exceptions import ActionException
from .core.base_migrations import BaseEventMigration, BaseMigration, BaseModelMigration
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
from .core.migration_handler import (
    MigrationHandler,
    MigrationHandlerImplementationMemory,
    MigrationState,
)
from .core.migration_keyframes import (
    BaseMigrationKeyframeException,
    MigrationKeyframeAccessor,
    MigrationKeyframeModelDeleted,
    MigrationKeyframeModelDoesNotExist,
    MigrationKeyframeModelNotDeleted,
)
from .core.migration_logger import PrintFunction
from .core.setup import setup
from .migrate import MigrationWrapper
from .util.add_field_migration import AddFieldMigration
from .util.add_fields_migration import AddFieldsMigration, Calculated
from .util.remove_fields_migration import RemoveFieldsMigration
from .util.rename_field_migration import RenameFieldMigration


def get_backend_migration_index() -> int:
    migration_classes = MigrationWrapper.load_migrations()

    backend_migration_index = 1
    for migration_class in migration_classes:
        backend_migration_index = max(
            backend_migration_index, migration_class().target_migration_index
        )
    return backend_migration_index


def get_datastore_migration_index() -> int:
    read_db = injector.get(ReadDatabase)
    with read_db.get_context():
        datastore_migration_index = read_db.get_current_migration_index()
    return datastore_migration_index


def assert_migration_index() -> None:
    connection = injector.get(ConnectionHandler)
    with connection.get_connection_context():
        if connection.query_single_value("select count(*) from positions", []) == 0:
            return  # Datastore is empty; nothing to check.

    datastore_migration_index = get_datastore_migration_index()

    if datastore_migration_index == -1:
        return  # Datastore is up-to-date; nothing to do.

    backend_migration_index = get_backend_migration_index()

    if backend_migration_index > datastore_migration_index:
        raise ActionException(
            f"Missing {backend_migration_index-datastore_migration_index} migrations to apply."
        )

    if backend_migration_index < datastore_migration_index:
        raise ActionException(
            f"Migration indices do not match: Datastore has {datastore_migration_index} and the backend has {backend_migration_index}"
        )
