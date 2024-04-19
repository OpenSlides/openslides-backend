from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.writer.core import Database
from openslides_backend.migrations import MigrationHandler, MigrationSetupException
from openslides_backend.migrations.core.migraters import (
    EventMigrater,
    EventMigraterImplementation,
    ModelMigrater,
    ModelMigraterImplementation,
)
from openslides_backend.migrations.core.migration_handler import (
    MigrationHandlerImplementation,
)
from openslides_backend.migrations.core.migration_logger import (
    MigrationLogger,
    MigrationLoggerImplementation,
)
from openslides_backend.migrations.core.migration_reader import MigrationReader
from tests.datastore import reset_di  # noqa

from ..util import get_noop_event_migration, get_noop_model_migration


@pytest.fixture(autouse=True)
def migration_handler(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, MagicMock)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register_as_singleton(Database, MagicMock)
    injector.register_as_singleton(MigrationReader, MagicMock)
    injector.register_as_singleton(MigrationLogger, MigrationLoggerImplementation)
    injector.register_as_singleton(EventMigrater, EventMigraterImplementation)
    injector.register_as_singleton(ModelMigrater, ModelMigraterImplementation)
    injector.register_as_singleton(MigrationHandler, MigrationHandlerImplementation)
    yield injector.get(MigrationHandler)


def test_no_migration_index(migration_handler):
    with pytest.raises(MigrationSetupException):
        migration_handler.register_migrations(get_noop_event_migration(None))


def test_migration_index_ok(migration_handler):
    migration_handler.register_migrations(
        get_noop_event_migration(2),
        get_noop_event_migration(3),
        get_noop_event_migration(4),
    )


def test_too_high_migration_index(migration_handler):
    with pytest.raises(MigrationSetupException):
        migration_handler.register_migrations(get_noop_event_migration(3))


def test_too_low_migration_index(migration_handler):
    with pytest.raises(MigrationSetupException):
        migration_handler.register_migrations(
            get_noop_event_migration(1), get_noop_event_migration(2)
        )


def test_non_linear_migration_index(migration_handler):
    with pytest.raises(MigrationSetupException):
        migration_handler.register_migrations(
            get_noop_event_migration(2), get_noop_event_migration(4)
        )


def test_duplicate_register(migration_handler):
    migration_handler.register_migrations(get_noop_event_migration(2))
    with pytest.raises(MigrationSetupException):
        migration_handler.register_migrations(get_noop_event_migration(2))


def test_event_after_model_migration(migration_handler):
    with pytest.raises(MigrationSetupException):
        migration_handler.register_migrations(
            get_noop_event_migration(2),
            get_noop_model_migration(3),
            get_noop_event_migration(4),
        )
