from datetime import datetime

from openslides_backend.datastore.shared.di import service_as_factory
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.services import ReadDatabase
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    Position,
    is_reserved_field,
)
from openslides_backend.shared.typing import Model

from ..events import BaseEvent, CreateEvent
from ..migration_keyframes import InitialMigrationKeyframeModifier
from ..migration_logger import MigrationLogger
from .event_migrater import RawPosition
from .memory_migrater import MemoryMigrater
from .migrater import EventMigrater


@service_as_factory
class EventMigraterImplementationMemory(EventMigrater, MemoryMigrater):
    """
    This migrater is made for in memory migrations of meeting imports.
    The whole import will be imported to 1 position. Unlike the database
    migration, there is no need to have keyframes/baselines for all
    migrationlevels for the last position.
    """

    read_database: ReadDatabase
    connection: ConnectionHandler
    logger: MigrationLogger

    def migrate(self) -> None:
        position = RawPosition(
            position=1,
            migration_index=self.start_migration_index,
            timestamp=datetime.now(),
            user_id=0,
            information=None,
        )
        self.migrate_position(position, 0)

    def migrate_position(
        self, position: RawPosition, last_position_value: Position
    ) -> None:
        """
        Used for in memory migration of import data.
        All import data will be imported at one position.
        """
        self.logger.info(
            f"Migrate import data from MI {self.start_migration_index} to MI {self.target_migration_index} ..."
        )
        events: list[BaseEvent] = [
            CreateEvent(
                fqid,
                {
                    field: value
                    for field, value in model.items()
                    if not is_reserved_field(field) and value is not None
                },
            )
            for fqid, model in self.models.items()
        ]

        for (
            source_migration_index,
            target_migration_index,
            migration,
        ) in self.get_migrations(self.start_migration_index):
            old_accessor, new_accessor = self.get_accessors(
                last_position_value,
                source_migration_index,
                target_migration_index,
                position.position,
            )

            events = migration.migrate(
                events, old_accessor, new_accessor, position.to_position_data()
            )
            self.migrated_models = new_accessor.models

    def get_migrated_models(self) -> dict[FullQualifiedId, Model]:
        return self.migrated_models

    def get_accessors(
        self,
        last_position_value: Position,
        source_migration_index: int,
        target_migration_index: int,
        position: Position,
        _: bool = False,
    ) -> tuple[InitialMigrationKeyframeModifier, InitialMigrationKeyframeModifier]:
        old_accessor = InitialMigrationKeyframeModifier(
            self.connection,
            last_position_value,
            source_migration_index,
            position,
        )
        new_accessor = InitialMigrationKeyframeModifier(
            self.connection,
            last_position_value,
            target_migration_index,
            position,
        )
        return old_accessor, new_accessor
