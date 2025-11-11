class MigrationException(Exception):
    pass


class MigrationSetupException(MigrationException):
    pass


class MismatchingMigrationIndicesException(MigrationException):
    pass


class InvalidMigrationCommand(MigrationException):
    def __init__(self, command: str) -> None:
        super().__init__(f"Invalid migration command: {command}")


class BadMigrationModule(MigrationException):
    pass
