from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.migrations.core.migration_logger import (
    MigrationLogger,
    MigrationLoggerImplementation,
)
from tests.datastore import reset_di  # noqa


@pytest.fixture()
def migration_logger(reset_di):  # noqa
    injector.register_as_singleton(MigrationLogger, MigrationLoggerImplementation)
    yield injector.get(MigrationLogger)


def test_print_info(migration_logger):
    message = MagicMock()
    print_mock = MagicMock()
    migration_logger.set_print_fn(print_mock)
    migration_logger.info(message)
    print_mock.assert_called_with(message)


def test_print_debug_verbose(migration_logger):
    migration_logger.set_verbose(True)
    message = MagicMock()
    print_mock = MagicMock()
    migration_logger.set_print_fn(print_mock)
    migration_logger.debug(message)
    print_mock.assert_called_with(message)


def test_print_debug_not_verbose(migration_logger):
    migration_logger.set_verbose(False)
    message = MagicMock()
    print_mock = MagicMock()
    migration_logger.set_print_fn(print_mock)
    migration_logger.debug(message)
    print_mock.assert_not_called()
