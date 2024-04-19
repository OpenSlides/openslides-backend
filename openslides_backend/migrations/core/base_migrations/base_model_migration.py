from openslides_backend.datastore.writer.core import BaseRequestEvent

from ..migration_reader import MigrationReader
from .base_migration import BaseMigration


class BaseModelMigration(BaseMigration):
    """The base class to represent a model migration."""

    reader: MigrationReader

    def migrate(self, reader: MigrationReader) -> list[BaseRequestEvent] | None:
        self.reader = reader
        return self.migrate_models()

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        """
        Migrates the models. The current models can be accessed via self.database. Should return
        a list of events with all changes to apply.
        """
