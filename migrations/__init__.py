from datastore.shared.di import injector
from datastore.shared.postgresql_backend import ConnectionHandler
from datastore.shared.services import ReadDatabase

from .migrate import load_migrations


class MissingMigrations(Exception):
    pass


class MisconfiguredMigrations(Exception):
    pass


def assert_migration_index() -> None:
    connection = injector.get(ConnectionHandler)
    with connection.get_connection_context():
        if connection.query_single_value("select count(*) from positions", []) == 0:
            return  # Datastore is empty; nothing to check.

    migration_classes = load_migrations()

    backend_migration_index = 1
    for migration_class in migration_classes:
        backend_migration_index = max(
            backend_migration_index, migration_class().target_migration_index
        )

    # Get the migration index from the datastore:
    read_db = injector.get(ReadDatabase)
    with read_db.get_context():
        datastore_migration_index = max(1, read_db.get_current_migration_index())

    if backend_migration_index > datastore_migration_index:
        raise MissingMigrations(
            f"Missing {backend_migration_index-datastore_migration_index} migrations to apply."
        )

    if backend_migration_index < datastore_migration_index:
        raise MisconfiguredMigrations(
            f"Migration indices do not match: Datastore has {datastore_migration_index} and the backend has {backend_migration_index}"
        )
