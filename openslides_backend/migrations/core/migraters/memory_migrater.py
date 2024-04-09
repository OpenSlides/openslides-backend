from openslides_backend.datastore.shared.typing import Fqid, Model

from .migrater import BaseMigrater


class MemoryMigrater(BaseMigrater):
    """
    This migrater is made for in memory migrations of meeting imports.
    The whole import will be imported to 1 position. Unlike the database
    migration, there is no need to have keyframes/baselines for all
    migrationlevels for the last position.
    """

    start_migration_index: int
    models: dict[Fqid, Model]

    def get_migrated_models(self) -> dict[Fqid, Model]:
        raise NotImplementedError()
