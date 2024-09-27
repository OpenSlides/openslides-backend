from importlib import import_module
from os import listdir
from re import Match, match

from openslides_backend.database.db_connection_handling import os_conn_pool

# relative path to the migrations
MIGRATIONS_RELATIVE_DIRECTORY_PATH = ""
LAST_NON_REL_MIGRATION = 53


class MigrationHelper:
    """
    Helper class containing static methods for handling the migrations. Reads and executes them.
    """

    migrations: dict = {}

    @staticmethod
    def run_migrations() -> None:
        """
        Runs the full migration process.

        Returns:
        - None
        """
        MigrationHelper.load_migrations()
        MigrationHelper.execute_migrations()

    @staticmethod
    def load_migrations() -> None:
        """
        Checks wether current migration_index is equal to or above the FIRST_REL_DB_MIGRATION and
        accesses MIGRATION_DIRECTORY_PATH. Lists every migration file above the migration_index
        and stores them in MigrationHelper.migrations for future reference.

        Returns:
        - None
        """
        migrations: list
        migration_file: str
        migration_index: int
        migration_number: int
        reMatch: Match[str] | None

        migration_index = MigrationHelper.pull_migration_index_from_db()

        assert (
            migration_index >= LAST_NON_REL_MIGRATION
        ), f"Migration Index {migration_index} should be at least {LAST_NON_REL_MIGRATION}."

        migrations = listdir(MIGRATIONS_RELATIVE_DIRECTORY_PATH)

        for n, migration in enumerate(migrations[:]):
            reMatch = match(r"(?P<migration>\d{4}_.*)\.py", migration)
            # \d{4}_.*\.py : 4 digits, 1 underscore, any characters, [dot]py
            if reMatch is not None:
                migration_file = reMatch.groupdict()["migration"]
                migration_number = int(migration_file[:4])
                if migration_number > migration_index:
                    MigrationHelper.migrations[migration_number] = migration

        MigrationHelper.migrations = dict(sorted(MigrationHelper.migrations.items()))

    @staticmethod
    def pull_migration_index_from_db() -> int:
        """
        Reads the current migration_index from the psql database.
        1. MAX(migration_index) of positions while position is used for the index
        2. migration_index from version after the second migration to eliminate the table position

        Returns:
        - migration_index : integer
        """
        migration_index: int

        with os_conn_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(migration_index) FROM positions;")
                row = cur.fetchone()
                if row is None:
                    cur.execute("SELECT migration_index FROM version;")
                    row = cur.fetchone()

                assert row is not None, "No migration_index could be found."

                # the row consists of only the column max, but it's presented as dictionary anyways
                migration_index = getattr(row, "max", 0)

        assert isinstance(
            migration_index, int
        ), f"Type {type(migration_index)} of migration_index must be int."

        return migration_index

    @staticmethod
    def execute_migrations() -> None:
        """
        Executes the migrations stored in MigrationHelper.migrations.
        Every migration could provide all of the three methods data_definition,
        data_manipulation and cleanup.

        Returns:
        - None
        """
        module_path: str
        module_name: str

        module_path = MIGRATIONS_RELATIVE_DIRECTORY_PATH.replace("/", ".")

        for index, migration in MigrationHelper.migrations.items():
            module_name = migration.replace(".py", "")
            migration_module = import_module(f"{module_path}{module_name}")
            if getattr(migration_module, "IN_MEMORY", False):
                migration_module.in_memory_method()
            else:
                # checks wether the methods are available and executes them.
                if callable(getattr(migration_module, "data_definition", None)):
                    migration_module.data_definition()
                if callable(getattr(migration_module, "data_manipulation", None)):
                    migration_module.data_manipulation()
                if callable(getattr(migration_module, "cleanup", None)):
                    migration_module.cleanup()

            # TODO In-Memory migration
