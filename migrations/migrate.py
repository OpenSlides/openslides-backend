import pkgutil
import sys
from argparse import ArgumentParser
from importlib import import_module
from typing import Any, List, Type

from datastore.migrations import BaseMigration, MigrationException, PrintFunction, setup


class BadMigrationModule(MigrationException):
    pass


class InvalidMigrationCommand(MigrationException):
    def __init__(self, command: str) -> None:
        super().__init__(f"Invalid migration command: {command}")


class MigrationWrapper:
    def __init__(self, verbose: bool = False, print_fn: PrintFunction = print) -> None:
        migrations = MigrationWrapper.load_migrations()
        self.handler = setup(verbose, print_fn)
        self.handler.register_migrations(*migrations)

    @staticmethod
    def load_migrations(
        base_migration_module_pypath: str = None,
    ) -> List[Type[BaseMigration]]:
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

        migration_classes: List[Type[BaseMigration]] = []
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
        if command == "migrate":
            self.handler.migrate()
        elif command == "finalize":
            self.handler.finalize()
        elif command == "reset":
            self.handler.reset()
        elif command == "clear-collectionfield-tables":
            self.handler.delete_collectionfield_aux_tables()
        elif command == "stats":
            return self.handler.get_stats()
        else:
            raise InvalidMigrationCommand(command)


def get_parser() -> ArgumentParser:
    parent_parser = ArgumentParser(
        description="Migration tool for allying migrations to the datastore."
    )
    parent_parser.add_argument(
        "--verbose",
        "-v",
        required=False,
        default=False,
        action="store_true",
        help="Enable verbose output",
    )
    subparsers = parent_parser.add_subparsers(title="commands", dest="command")
    subparsers.add_parser(
        "migrate",
        add_help=False,
        description="The migrate parser",
        help="Migrate the datastore.",
    )
    subparsers.add_parser(
        "finalize",
        add_help=False,
        description="The finalize parser",
        help="Finalize the datastore migrations.",
    )
    subparsers.add_parser(
        "reset",
        add_help=False,
        description="The reset parser",
        help="Reset all ongoing (not finalized) migrations.",
    )
    subparsers.add_parser(
        "clear-collectionfield-tables",
        add_help=False,
        description="The clear-collectionfield-tables parser",
        help="Clear all data from these auxillary tables. Can be done to clean up diskspace, but only when the datastore is offile.",
    )
    subparsers.add_parser(
        "stats",
        add_help=False,
        description="The stats parser",
        help="Print some stats about the current migration state.",
    )
    return parent_parser


def main() -> int:
    parser = get_parser()
    args = parser.parse_args()

    handler = MigrationWrapper(args.verbose)

    if not args.command:
        print("No command provided.\n")
        parser.print_help()
        return 1
    else:
        try:
            handler.execute_command(args.command)
        except InvalidMigrationCommand:
            print(f"Unknown command {args.command}\n")
            parser.print_help()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
