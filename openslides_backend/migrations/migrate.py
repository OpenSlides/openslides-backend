import logging
import os
import sys
from argparse import ArgumentParser

from dependency_injector import providers

from openslides_backend.migrations.migration_handler import InvalidMigrationCommand
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.shared.env import Environment


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
        "stats",
        add_help=False,
        description="The stats parser",
        help="Print some stats about the current migration state.",
    )
    return parent_parser


def main() -> int:
    parser = get_parser()
    args = parser.parse_args()

    manager = MigrationManager(
        Environment(os.environ), providers.DependenciesContainer(), logging
    )

    if not args.command:
        print("No command provided.\n")
        parser.print_help()
        return 1
    else:
        try:
            manager.handle_request(args.command)
        except InvalidMigrationCommand:
            print(f"Unknown command {args.command}\n")
            parser.print_help()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
