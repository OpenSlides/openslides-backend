import pkgutil
from collections.abc import Callable
from importlib import import_module
from typing import Any

from openslides_backend.migrations import BaseMigration, MigrationException
from openslides_backend.wsgi import OpenSlidesBackendServices

PrintFunction = Callable[..., None]


class BadMigrationModule(MigrationException):
    pass


class InvalidMigrationCommand(MigrationException):
    def __init__(self, command: str) -> None:
        super().__init__(f"Invalid migration command: {command}")


class MigrationWrapper:

    def __init__(
        self,
        verbose: bool = False,
        print_fn: PrintFunction = print,
    ) -> None:
        services = OpenSlidesBackendServices()
        migrations = MigrationWrapper.load_migrations()
        # TODO: There used to be code here that setup some dependency injections
        # The former initialization of the migration handler did as well.

    @staticmethod
    def load_migrations(
        base_migration_module_pypath: str | None = None,
    ) -> list[type[BaseMigration]]:
        if not base_migration_module_pypath:
            base_module = __name__.rsplit(".", 1)[0]
            if base_module == "__main__":
                base_migration_module_pypath = "migrations"
            else:
                base_migration_module_pypath = base_module + ".migrations"
        base_migration_module = import_module(base_migration_module_pypath)

        module_names = {
            name
            for _, name, is_pkg in pkgutil.iter_modules(base_migration_module.__path__)  # type: ignore
            if not is_pkg
        }

        migration_classes: list[type[BaseMigration]] = []
        for module_name in module_names:
            module_pypath = f"{base_migration_module_pypath}.{module_name}"
            migration_module = import_module(module_pypath)
            if not hasattr(migration_module, "Migration"):
                raise BadMigrationModule(
                    f"The module {module_pypath} does not have a class called 'Migration'"
                )
            migration_class = migration_module.Migration  # type: ignore
            if not issubclass(migration_class, BaseMigration):
                raise BadMigrationModule(
                    f"The class 'Migration' in module {module_pypath} does not inherit from 'BaseMigration'"
                )
            migration_classes.append(migration_class)
        return migration_classes

    def execute_command(self, command: str) -> Any:
        pass

    #     if command == "migrate":
    #         self.handler.migrate()
    #     elif command == "finalize":
    #         self.handler.finalize()
    #     elif command == "reset":
    #         self.handler.reset()
    #     elif command == "clear-collectionfield-tables":
    #         self.handler.delete_collectionfield_aux_tables()
    #     elif command == "stats":
    #         self.handler.print_stats()
    #     else:
    #         raise InvalidMigrationCommand(command)
