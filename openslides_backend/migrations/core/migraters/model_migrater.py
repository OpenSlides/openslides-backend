from openslides_backend.datastore.shared.di import service_as_factory
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.datastore.writer.core import Database
from openslides_backend.migrations.core.migration_reader import MigrationReader

from ..migration_logger import MigrationLogger
from .migrater import ModelMigrater


@service_as_factory
class ModelMigraterImplementation(ModelMigrater):
    reader: MigrationReader
    read_database: ReadDatabase
    write_database: Database
    connection: ConnectionHandler
    logger: MigrationLogger

    def migrate(self) -> None:
        with self.connection.get_connection_context():
            current_migration_index = self.read_database.get_current_migration_index()
        self.logger.info(
            f"Migrating models from MI {current_migration_index} to MI {self.target_migration_index} ..."
        )
        for _, target_migration_index, migration in self.get_migrations(
            current_migration_index
        ):
            with self.connection.get_connection_context():
                events = migration.migrate(self.reader)
                if events:
                    self.write_database.insert_events(
                        events, target_migration_index, None, 0
                    )
