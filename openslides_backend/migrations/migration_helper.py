import os
from enum import StrEnum
from importlib import import_module
from io import StringIO
from re import Match, match
from threading import Thread
from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb

from openslides_backend.migrations.exceptions import MigrationException
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
    MIGRATION_FINISHED = "migration_finished"
    FINALIZED = "finalized"


class MigrationCommand(StrEnum):
    MIGRATE = "migrate"
    RESET = "reset"
    STATS = "stats"
    PROGRESS = "progress"


# relative path to the migrations
MIGRATIONS_PATH = "openslides_backend/migrations/"
MODULE_PATH = MIGRATIONS_PATH.replace("/", ".")
MIN_NON_REL_MIGRATION = 73


class MigrationHelper:
    """
    Helper class containing static methods for handling the migrations. Reads and executes them.
    """

    migrations: dict = {}
    migrate_thread: Thread | None = None
    migrate_thread_stream: StringIO | None = None
    migrate_thread_stream_read_pos: int = 0
    migrate_thread_stream_can_be_closed = False
    migrate_thread_exception: Exception | None = None

    @staticmethod
    def write_line(message: str) -> None:
        """
        Writes a single line with \n to the migration threads io stream.
        """
        assert (stream := MigrationHelper.migrate_thread_stream)
        stream.write(message + "\n")

    @staticmethod
    def read_stream(all: bool = False) -> str:
        """
        Reads all lines since the last time reading.
        If `all` is set, all lines present in buffer are returned without
        - moving the cursor on the stream
        - or updating migrate_thread_stream_read_pos.
        """
        assert (stream := MigrationHelper.migrate_thread_stream)

        if all:
            return stream.getvalue()

        stream.seek(MigrationHelper.migrate_thread_stream_read_pos)
        result = stream.read()
        MigrationHelper.migrate_thread_stream_read_pos = stream.tell()
        return result

    @staticmethod
    def close_migrate_thread_stream() -> None:
        """
        Closes the migration threads io stream. Also deletes all possible migrate thread exceptions
        """
        if (
            MigrationHelper.migrate_thread_stream_can_be_closed
            and MigrationHelper.migrate_thread_stream
        ):
            MigrationHelper.migrate_thread_stream.close()
            MigrationHelper.migrate_thread_stream = None
            MigrationHelper.migrate_thread_stream_can_be_closed = False
            MigrationHelper.migrate_thread_stream_read_pos = 0
            MigrationHelper.migrate_thread_exception = None

    @staticmethod
    def load_migrations() -> None:
        """
        Checks whether current migration_index is equal to or above the FIRST_REL_DB_MIGRATION and
        accesses MIGRATION_DIRECTORY_PATH. Lists every migration file above the MIN_NON_REL_MIGRATION
        and stores them in MigrationHelper.migrations for future reference.

        Returns:
        - None
        """
        files_and_folders: list
        migration_name: str
        migration_number: int
        migration_dict = {}
        re_match: Match[str] | None

        files_and_folders = os.listdir(MIGRATIONS_PATH)

        for file_or_folder in files_and_folders:
            if os.path.isdir(os.path.join(MIGRATIONS_PATH, file_or_folder)):
                re_match = match(r"mig_(?P<migration>\d{4}_.*)", file_or_folder)
                # mig_ matches literaly and \d{4}_.* : 4 digits, 1 underscore, any characters
                if re_match is not None:
                    migration_name = re_match.groupdict()["migration"]
                    migration_number = int(migration_name[:4])
                    if migration_number >= 100:
                        migration_dict[migration_number] = file_or_folder
        MigrationHelper.migrations = dict(sorted(migration_dict.items()))

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
            "No unfinalized migration index could be acquired from database."
        )

    @staticmethod
    def get_indices_from_database(curs: Cursor[DictRow]) -> list[int]:
        """
        Gets all indices stored in the version table.
        """
        if tmp := curs.execute("SELECT migration_index FROM version;").fetchall():
            return [elem.get("migration_index", 0) for elem in tmp]
        raise MigrationException("No migration index could be acquired from database.")

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
            return tmp.get("max", MIN_NON_REL_MIGRATION)
        raise MigrationException(
            "Requested migration indices are not available in version table."
        )

    @staticmethod
    def get_last_migration_directory() -> str:
        """Returns the directory to the last migration. Currently only supports numbers until 1099."""
        idx_as_string = str(MigrationHelper.get_backend_migration_index())
        for name in os.listdir(MIGRATIONS_PATH):
            if idx_as_string in name:
                return name
        raise Exception("Could not find last migration directory.")

    @staticmethod
    def get_backend_migration_index() -> int:
        MigrationHelper.load_migrations()
        return max(MigrationHelper.migrations)

    @staticmethod
    def assert_failed_state(curs: Cursor[DictRow]) -> None:
        if tmp := curs.execute(
            "SELECT migration_index FROM version WHERE migration_state = %s;",
            (MigrationState.MIGRATION_FAILED,),
        ).fetchall():
            raise MigrationException(
                f"Migration has failed for {', '.join(str(d['migration_index']) for d in tmp)}."
            )

    @staticmethod
    def assert_migration_index(curs: Cursor[DictRow]) -> None:
        """
        Asserts that backend and database migration indices are identical.
        """
        MigrationHelper.assert_failed_state(curs)
        database_migration_index = MigrationHelper.get_database_migration_index(curs)
        backend_migration_index = MigrationHelper.get_backend_migration_index()

        if backend_migration_index > database_migration_index:
            raise ActionException(
                f"Missing {backend_migration_index-database_migration_index} migrations to be applied."
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
            values=sql.SQL(", ").join(sql.Placeholder() for _ in params),
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
            assert row and row.get(
                "max"
            ), "No migration_index could be could be found in positions."
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
        FINALIZED, MIGRATION_FINISHED, MIGRATION_REQUIRED, MIGRATION_RUNNING, MIGRATION_FAILED.
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
        # 1. migration, 2. finalization | both: failed > running > required
        for state in [
            MigrationState.MIGRATION_FAILED,
            MigrationState.MIGRATION_RUNNING,
            MigrationState.MIGRATION_REQUIRED,
            MigrationState.MIGRATION_FINISHED,
        ]:
            if state in states:
                return state
        raise MigrationException("No such State implemented.")

    @staticmethod
    def get_migration_class(package_name: str) -> Any:
        """
        Returns the class Migration within the specified module.
        """
        return getattr(
            import_module(f"{MODULE_PATH}{package_name}.migration"), "Migration"
        )

    @staticmethod
    def get_public_tables(curs: Cursor[DictRow]) -> set[str]:
        """Returns all tables of the schema 'public' except for version and notify table"""
        curs.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
        ).fetchone()
        return {
            name
            for row in curs.fetchall()
            if (name := row["tablename"])
            not in ("version", "os_notify_log_t", "truncate_tables")
        }

    @staticmethod
    def get_replace_tables(
        migration_number: int,
    ) -> dict[str, dict[str, str | list[str]]]:
        """
        Returns the replace tables. This is in its current state merely a collection of the migrated tables.
        """
        module_name = MigrationHelper.migrations[migration_number]
        migration_class = MigrationHelper.get_migration_class(module_name)
        return {col: {} for col in set(migration_class.ORIGIN_COLLECTIONS)}

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
        curs: Cursor[DictRow], migration_state: MigrationState | None = None
    ) -> dict[str, Any]:
        """
        Returns the replace tables, mapping the collection to its migration copies,
        stored in the database unified for all indices with `migration_state`.
        If no `migration_state` was given: stored in the database unified for all -non- migrated indices.
        """
        if not migration_state:
            migration_state = MigrationState.FINALIZED
            operator = "!="
        else:
            operator = "="
        rows = curs.execute(
            f"SELECT replace_tables FROM version WHERE migration_state {operator} %s",
            [migration_state],
        )
        return {
            collection: replace_tables
            for row in rows
            for collection, replace_tables in row["replace_tables"].items()
        }

    @staticmethod
    def copy_table(
        curs: Cursor[DictRow], table_name: str, target_table_name: str
    ) -> None:
        """
        Copies the table with its definition and rows. Does not copy triggers and foreign key constraints.
        For use in data_preparation step of migration.
        """
        target_table = sql.Identifier(target_table_name)
        table_t = sql.Identifier(table_name)
        curs.execute(
            sql.SQL(
                "CREATE TABLE {target_table} (LIKE {table_t} INCLUDING ALL);"
            ).format(target_table=target_table, table_t=table_t)
        )

        fields = curs.execute(sql.SQL("""
                SELECT *
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = {table};
                """).format(table=table_name)).fetchall()
        curs.execute(
            sql.SQL(
                "INSERT INTO {target_table} ({fields}) SELECT {fields} FROM {table_t};"
            ).format(
                target_table=target_table,
                table_t=table_t,
                fields=sql.SQL(", ").join(
                    sql.SQL(data["column_name"])
                    for data in fields
                    if data["is_generated"] != "ALWAYS"
                ),
            )
        )
