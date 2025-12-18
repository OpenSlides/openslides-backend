class MigrationException(Exception):
    pass


class MigrationSetupException(MigrationException):
    pass


class MismatchingMigrationIndicesException(MigrationException):
    pass
