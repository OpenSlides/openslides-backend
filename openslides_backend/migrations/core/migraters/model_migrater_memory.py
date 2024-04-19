from openslides_backend.datastore.shared.di import service_as_factory
from openslides_backend.datastore.writer.postgresql_backend import (
    EventTranslator,
    apply_event_to_models,
)
from openslides_backend.migrations.core.migration_reader import (
    MigrationReader,
    MigrationReaderImplementationMemory,
)
from openslides_backend.shared.patterns import FullQualifiedId
from openslides_backend.shared.typing import Model

from ..migration_logger import MigrationLogger
from .memory_migrater import MemoryMigrater
from .migrater import ModelMigrater


@service_as_factory
class _ModelMigraterImplementationMemory(ModelMigrater, MemoryMigrater):
    """
    Dummy class to inject the correct reader, but have the typing correct in the actual
    implementation.
    """

    reader: MigrationReader
    translator: EventTranslator
    logger: MigrationLogger


class ModelMigraterImplementationMemory(_ModelMigraterImplementationMemory):
    reader: MigrationReaderImplementationMemory

    def migrate(self) -> None:
        self.reader.models = self.models

        self.logger.info(
            f"Migrate import data from MI {self.start_migration_index} to MI {self.target_migration_index} ..."
        )

        for _, _, migration in self.get_migrations(self.start_migration_index):
            events = migration.migrate(self.reader)
            if events:
                for event in events:
                    db_events = self.translator.translate(event, self.models)
                    for db_event in db_events:
                        apply_event_to_models(db_event, self.models)

    def get_migrated_models(self) -> dict[FullQualifiedId, Model]:
        return self.models
