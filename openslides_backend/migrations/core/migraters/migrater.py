from collections.abc import Iterable
from typing import Generic, Protocol, TypeVar

from openslides_backend.datastore.shared.di import service_interface
from openslides_backend.migrations.core.base_migrations.base_event_migration import (
    BaseEventMigration,
)
from openslides_backend.migrations.core.base_migrations.base_model_migration import (
    BaseModelMigration,
)
from openslides_backend.migrations.core.migration_logger import MigrationLogger

from ..base_migrations import BaseMigration

T = TypeVar("T", bound=BaseMigration)


class BaseMigrater(Protocol, Generic[T]):
    target_migration_index: int
    migrations: dict[int, BaseMigration]
    logger: MigrationLogger
    migration_type: type[T]  # must be set by the subclass

    def init(
        self,
        target_migration_index: int,
        migrations: dict[int, BaseMigration],
    ) -> None:
        self.target_migration_index = target_migration_index
        self.migrations = migrations

    def get_migrations(
        self, start_migration_index: int
    ) -> Iterable[tuple[int, int, T]]:
        for source_migration_index in range(
            start_migration_index, self.target_migration_index
        ):
            target_migration_index = source_migration_index + 1
            self.logger.debug(
                f"\tRunning migration with target migration index {target_migration_index}"
            )

            migration = self.migrations[target_migration_index]
            assert isinstance(migration, self.migration_type)
            yield source_migration_index, target_migration_index, migration

    def migrate(self) -> None:
        """
        Runs the actual migrations of the datastore up to the target migration index.
        """


@service_interface
class EventMigrater(BaseMigrater[BaseEventMigration]):
    """Marker class for an event migrater."""

    migration_type = BaseEventMigration


@service_interface
class ModelMigrater(BaseMigrater[BaseModelMigration]):
    """Marker class for a model migrater."""

    migration_type = BaseModelMigration
