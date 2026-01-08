from enum import StrEnum
from importlib import import_module
from io import StringIO
from os import listdir
from re import Match, match
from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb

from openslides_backend.migrations.core.exceptions import MigrationException
from openslides_backend.models.base import model_registry
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)

from ..shared.exceptions import ActionException

OLD_TABLES = (
    "models",
    "events",
    "positions",
    "id_sequences",
    "collectionfields",
    "events_to_collectionfields",
    "migration_keyframes",
    "migration_keyframe_models",
    "migration_events",
    "migration_positions",
)


class MigrationState(StrEnum):
    """
    All possible migration states, ordered by priority. E.g. a running migration implicates that
    migrations are required and required migration implicates that finalization is also required.
    """

    MIGRATION_REQUIRED = "migration_required"
    MIGRATION_RUNNING = "migration_running"
    MIGRATION_FAILED = "migration_failed"
    FINALIZATION_REQUIRED = "finalization_required"
    FINALIZATION_RUNNING = "finalization_running"
    FINALIZED = "finalized"
    FINALIZATION_FAILED = "finalization_failed"


class MigrationCommand(StrEnum):
    MIGRATE = "migrate"
    FINALIZE = "finalize"
    RESET = "reset"
    STATS = "stats"
    PROGRESS = "progress"


# relative path to the migrations
MIGRATIONS_PATH = "openslides_backend/migrations/migrations/"
MODULE_PATH = MIGRATIONS_PATH.replace("/", ".")
LAST_NON_REL_MIGRATION = 73


class MigrationHelper:
    """
    Helper class containing static methods for handling the migrations. Reads and executes them.
    """

    migrations: dict = {}
    migrate_thread_stream: StringIO | None = None
    migrate_thread_stream_can_be_closed = False
    migrate_thread_exception: Exception | None = None

    @staticmethod
    def write_line(message: str) -> None:
        """
        Writes a single line with \n to the migration threads io stream.
        """
        assert MigrationHelper.migrate_thread_stream
        MigrationHelper.migrate_thread_stream.write(message + "\n")

    @staticmethod
    def load_migrations() -> None:
        """
        Checks wether current migration_index is equal to or above the FIRST_REL_DB_MIGRATION and
        accesses MIGRATION_DIRECTORY_PATH. Lists every migration file above the LAST_NON_REL_MIGRATION
        and stores them in MigrationHelper.migrations for future reference.

        Returns:
        - None
        """
        migrations: list
        migration_file: str
        migration_number: int
        reMatch: Match[str] | None

        migrations = listdir(MIGRATIONS_PATH)

        for migration in migrations:
            reMatch = match(r"(?P<migration>\d{4}_.*)\.py", migration)
            # \d{4}_.*\.py : 4 digits, 1 underscore, any characters, [dot]py
            if reMatch is not None:
                migration_file = reMatch.groupdict()["migration"]
                migration_number = int(migration_file[:4])
                if migration_number > LAST_NON_REL_MIGRATION:
                    MigrationHelper.migrations[migration_number] = migration[:-3]
        MigrationHelper.migrations = dict(sorted(MigrationHelper.migrations.items()))

    @staticmethod
    def add_new_migrations_to_version() -> None:
        """
        Adds new migrations to the version table with state MIGRATION_REQUIRED if the index didn't exist yet.
        """
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                database_indices = MigrationHelper.get_indices_from_database(curs)
                for migration_index in MigrationHelper.migrations:
                    if migration_index not in database_indices:
                        replace_tables = MigrationHelper.get_replace_tables(
                            migration_index
                        )
                        MigrationHelper.set_database_migration_info(
                            curs,
                            migration_index,
                            MigrationState.MIGRATION_REQUIRED,
                            replace_tables,
                        )

    @staticmethod
    def get_unfinalized_indices(curs: Cursor[DictRow]) -> list[int]:
        """
        Gets all indices stored in the version table.
        """
        if tmp := curs.execute(
            "SELECT migration_index FROM version WHERE migration_state != %s;",
            (MigrationState.FINALIZED,),
        ).fetchall():
            return [elem.get("migration_index", 0) for elem in tmp]
        raise MigrationException(
            "No migration index could not be acquired from database."
        )

    @staticmethod
    def get_indices_from_database(curs: Cursor[DictRow]) -> list[int]:
        """
        Gets all indices stored in the version table.
        """
        if tmp := curs.execute("SELECT migration_index FROM version;").fetchall():
            return [elem.get("migration_index", 0) for elem in tmp]
        raise MigrationException(
            "No migration index could not be acquired from database."
        )

    @staticmethod
    def get_database_migration_states(
        curs: Cursor[DictRow], indices: list[int]
    ) -> dict[int, MigrationState]:
        """
        Gets the states per passed migration index.
        """
        if tmp := curs.execute(
            sql.SQL(
                "SELECT migration_index, migration_state FROM version WHERE migration_index = ANY("
            )
            + sql.Placeholder()
            + sql.SQL(");"),
            (indices,),
        ).fetchall():
            return {
                elem.get("migration_index", 0): elem.get("migration_state", "")
                for elem in tmp
            }
        else:
            raise MigrationException(
                "Requested migration indices are not available in version table."
            )

    @staticmethod
    def get_database_migration_index(curs: Cursor[DictRow]) -> int:
        """
        Returns the maximum migration index which is in state FINALIZED.
        """
        if tmp := curs.execute(
            "SELECT MAX(migration_index) FROM version WHERE migration_state = %s;",
            (MigrationState.FINALIZED,),
        ).fetchone():
            return tmp.get("max") or LAST_NON_REL_MIGRATION
        raise MigrationException(
            "Requested migration indices are not available in version table."
        )

    @staticmethod
    def get_backend_migration_index() -> int:
        MigrationHelper.load_migrations()
        return max(MigrationHelper.migrations)

    @staticmethod
    def assert_migration_index(curs: Cursor[DictRow]) -> None:
        """
        Asserts that backend and database migration indices are identical.
        """
        database_migration_index = MigrationHelper.get_database_migration_index(curs)
        backend_migration_index = MigrationHelper.get_backend_migration_index()

        if backend_migration_index > database_migration_index:
            raise ActionException(
                f"Missing {backend_migration_index-database_migration_index} migrations to apply."
            )

        if backend_migration_index < database_migration_index:
            raise ActionException(
                f"Migration indices do not match: Database has {database_migration_index} and the backend has {backend_migration_index}"
            )

    @staticmethod
    def set_database_migration_info(
        curs: Cursor[DictRow],
        migration_index: int,
        state: str,
        replace_tables: dict[str, dict[str, str | list[str]]] | None = None,
    ) -> None:
        """
        Overwrites the databases migration info in the version table at the given migration index and commits the transaction.
        """
        params = {
            "migration_index": migration_index,
            "migration_state": state,
        }
        if replace_tables is not None:
            params["replace_tables"] = Jsonb(replace_tables)
        updates = [
            sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(k), sql.Identifier(k))
            for k in params
            if k != "migration_index"
        ]
        statement = sql.SQL(
            "INSERT INTO version ({fields}) VALUES ({values}) "
            "ON CONFLICT (migration_index) DO UPDATE SET {updates}"
        ).format(
            fields=sql.SQL(", ").join(sql.Identifier(k) for k in params),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in range(len(params))),
            updates=sql.SQL(", ").join(updates),
        )
        curs.execute(statement, tuple(params.values()))
        curs.connection.commit()

    @staticmethod
    def table_exists(curs: Cursor[DictRow], table_name: str) -> bool:
        """
        Returns True if the passed table exists in the database.
        """
        version_table_exists = curs.execute(
            "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = %s);",
            (table_name,),
        ).fetchone()
        assert (
            version_table_exists
        ), "Something really blew up checking the version tables existence."
        return version_table_exists["exists"]

    @staticmethod
    def pull_migration_index_from_db(curs: Cursor[DictRow]) -> int:
        """
        Reads the current migration_index from the psql database.
        1. MAX(migration_index) of positions while position is still used for the index
        2. MAX(migration_index) from version after the 'relational schema' is applied

        Returns:
        - migration_index : integer the migration index or 0 if this must be a fresh install.
        """
        migration_index: int
        if MigrationHelper.table_exists(curs, "version"):
            migration_index = MigrationHelper.get_database_migration_index(curs)
        elif MigrationHelper.table_exists(curs, "positions"):
            row = curs.execute("SELECT MAX(migration_index) FROM positions;").fetchone()
            assert row, "No migration_index could be found."
            # the row consists of only the column max, but it's presented as dictionary anyways
            migration_index = row["max"]
        else:
            migration_index = 0
        assert isinstance(
            migration_index, int
        ), f"Type {type(migration_index)} of migration_index must be int."

        return migration_index

    @staticmethod
    def get_migration_state(curs: Cursor[DictRow]) -> MigrationState:
        """
        Returns the highest MigrationState among all migrations in the ascending order of
        FINALIZED, FINALIZATION_REQUIRED, MIGRATION_REQUIRED, MIGRATION_RUNNING.
        """
        states_and_indices = curs.execute(
            sql.SQL(
                "SELECT migration_index, migration_state FROM version WHERE migration_state != %s"
            ),
            (MigrationState.FINALIZED,),
        ).fetchall()
        if not states_and_indices:
            return MigrationState.FINALIZED
        states = {elem.get("migration_state") for elem in states_and_indices}
        # 1. migration, 2. finalization -> failed > running > required
        for state in [
            MigrationState.MIGRATION_FAILED,
            MigrationState.MIGRATION_RUNNING,
            MigrationState.MIGRATION_REQUIRED,
            MigrationState.FINALIZATION_FAILED,
            MigrationState.FINALIZATION_RUNNING,
            MigrationState.FINALIZATION_REQUIRED,
        ]:
            if state in states:
                return state
        raise MigrationException("No such State implemented.")

    @staticmethod
    def get_public_tables(curs: Cursor[DictRow]) -> list[str]:
        """Returns all tables of the schema 'public' except for version and notify table"""
        curs.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
        ).fetchone()
        return [
            name
            for row in curs.fetchall()
            if (name := row["tablename"])
            not in ("version", "os_notify_log_t", "truncate_tables")
        ]

    @staticmethod
    def get_replace_tables(
        migration_number: int,
    ) -> dict[str, dict[str, str | list[str]]]:
        """
        Returns the replace tables mapping origin table to its migration copy.
        """
        module_name = MigrationHelper.migrations[migration_number]
        migration_module = import_module(f"{MODULE_PATH}{module_name}")
        return {
            col: {
                "table": col + "_m",
                "view": col + "vm",
                "im_tables": [
                    field.write_fields[0]
                    for field in model_registry[col]().get_relation_fields()
                    if field.write_fields
                ],
            }
            for col in migration_module.ORIGIN_COLLECTIONS
        }

    @staticmethod
    def get_replace_tables_from_database(
        curs: Cursor[DictRow], migration_number: int
    ) -> dict[str, Any]:
        """
        Returns the migration indexes replace tables, mapping the collection to its
        migration copies, stored in the database.
        """
        if replace_tables := curs.execute(
            f"SELECT replace_tables FROM version WHERE migration_index = {migration_number};"
        ).fetchone():
            return replace_tables["replace_tables"]
        raise MigrationException("Could not retrieve replace tables from database.")

    @staticmethod
    def get_unified_replace_tables_from_database(
        curs: Cursor[DictRow],
    ) -> tuple[dict[str, Any], list[int]]:
        """
        Returns the replace tables, mapping the collection to its migration copies,
        stored in the database unified for all -non- migrated indices.
        Returns the list of used (unmigrated) migration indices as a side product.
        """
        current_mi = MigrationHelper.get_database_migration_index(curs)
        relevant_mis = [
            mi
            for mi in MigrationHelper.get_indices_from_database(curs)
            if mi > current_mi
        ]
        return (
            {
                collection: r_tables
                for migration_number in relevant_mis
                for collection, r_tables in MigrationHelper.get_replace_tables_from_database(
                    curs, migration_number
                ).items()
            },
            relevant_mis,
        )
