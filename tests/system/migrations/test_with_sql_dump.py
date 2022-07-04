import pytest
from datastore.migrations.core.migration_handler import MigrationHandler
from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler

from openslides_backend.migrations.migrate import MigrationWrapper


@pytest.mark.skip()
def test_with_sql_dump(write, finalize, assert_model):
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        with connection_handler.get_current_connection().cursor() as cursor:
            cursor.execute(open("tests/dump.sql", "r").read(), [])
    migration_handler = injector.get(MigrationHandler)
    migration_handler.register_migrations(
        *MigrationWrapper.load_migrations("migrations")
    )
    migration_handler.finalize()
