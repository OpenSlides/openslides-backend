from ..exceptions import MigrationSetupException


class BaseMigration:
    """
    The base class to represent a migration. The `target_migration_index` must be set
    by each migration.
    """

    target_migration_index: int

    def __init__(self) -> None:
        self.name = self.__class__.__name__
        if self.target_migration_index == -1:
            raise MigrationSetupException(
                f"You need to specify target_migration_index of {self.name}"
            )
