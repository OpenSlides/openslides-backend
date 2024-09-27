import sys
from argparse import ArgumentParser

from openslides_backend.migrations.migration_wrapper import (
    InvalidMigrationCommand,
    MigrationWrapper,
)
from openslides_backend.migrations.migration_helper import (
    MigrationHelper
)


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
        help="Clear all data from these auxiliary tables. Can be done to clean up diskspace, but only when the datastore is offline.",
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
            MigrationHelper.run_migrations()
        except InvalidMigrationCommand:
            print(f"Unknown command {args.command}\n")
            parser.print_help()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
