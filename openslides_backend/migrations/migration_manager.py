from collections.abc import Callable
from io import StringIO
from textwrap import dedent
from threading import Thread
from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from openslides_backend.migrations.core.exceptions import (
    MigrationException,
    MismatchingMigrationIndicesException,
)
from openslides_backend.migrations.migration_helper import (
    LAST_NON_REL_MIGRATION,
    MigrationCommand,
    MigrationHelper,
    MigrationState,
)
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)

from ..shared.exceptions import View400Exception
from ..shared.interfaces.env import Env
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services
from .migration_handler import MigrationHandler

PrintFunction = Callable[..., None]

# Amount of time that should be waited for a result from the migrate thread before returning an empty result
THREAD_WAIT_TIME = 0.2


class MigrationManager:
    # TODO could be a singleton service
    handler: MigrationHandler

    def __init__(
        self,
        env: Env,
        services: Services,
        logging: LoggingModule,
        verbose: bool = False,
        print_fn: PrintFunction = print,
    ) -> None:
        """init"""
        self.verbose = verbose
        self.env = env
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)

        self.handler: MigrationHandler | None
        MigrationHelper.load_migrations()
        MigrationHelper.add_new_migrations_to_version()
        self.target_migration_index = MigrationHelper.get_backend_migration_index()

    def handle_progress_command(self) -> dict[str, Any]:
        if (
            MigrationHelper.get_migration_state(self.cursor)
            == MigrationState.MIGRATION_RUNNING
        ):
            if MigrationHelper.migrate_thread_stream:
                # Migration still running
                output = MigrationHelper.migrate_thread_stream.getvalue().split("\n")
                return {
                    "status": MigrationState.MIGRATION_RUNNING,
                    "output": f"{output[-2]}\n",
                    # The last line will always be an empty string.
                }
            else:
                raise RuntimeError("Invalid migration state")
        else:
            return MigrationHelper.get_migration_result(self.cursor)

    def get_stats(self) -> dict[str, Any]:
        """
        gets the stats:
        status: The current overall state.
        current_migration_index: The current migration index.
        target_migration_index: The current backend index that is targeted by the migrations.
        migratable_models: Rough amounts per collection to be migrated. Doesn't respect initial migration if on a higher target migration index.
        """

        def count(table: str, curs: Cursor[DictRow]) -> int:
            if current_migration_index == LAST_NON_REL_MIGRATION:
                response = self.cursor.execute(
                    sql.SQL(
                        "SELECT COUNT(*) FROM models WHERE fqid LIKE '{table}/%'"
                    ).format(table=sql.SQL(table[:-2]))
                ).fetchone()
            else:
                response = self.cursor.execute(
                    sql.SQL("SELECT COUNT(*) FROM {table}").format(
                        table=sql.Identifier(table)
                    )
                ).fetchone()
            if response:
                return response.get("count", 0)
            else:
                return 0

        current_migration_index = MigrationHelper.get_database_migration_index(
            self.cursor
        )

        migration_indices = MigrationHelper.get_indices_from_database(self.cursor)
        state_per_mi = MigrationHelper.get_database_migration_states(
            self.cursor, migration_indices
        )
        unmigrated_collections = {
            collection_table
            for mi in migration_indices
            if mi > current_migration_index
            if state_per_mi[mi] == MigrationState.MIGRATION_REQUIRED
            for collection_table in MigrationHelper.get_replace_tables(mi)
        }
        stats = {
            collection[:-2]: {"count": amount}
            for collection in unmigrated_collections
            if (amount := count(collection, self.cursor))
        }

        state = MigrationHelper.get_migration_state(self.cursor)

        # TODO enhance migratable models with numbers
        return {
            "status": state,
            "current_migration_index": current_migration_index,
            "target_migration_index": self.target_migration_index,
            "migratable_models": stats,
            **(
                {"exception": MigrationHelper.migrate_thread_exception}
                if MigrationHelper.migrate_thread_exception
                else {}
            ),
        }

    def print_stats(self) -> None:  # pragma: no cover
        stats = self.get_stats()
        if stats["current_migration_index"] == stats["target_migration_index"]:
            action = "The datastore is up-to-date"
        else:
            action = "Migration/Finalization is needed"
        if stats["status"] == MigrationState.NO_MIGRATION_REQUIRED:
            migration_action = "No action needed"
        elif stats["status"] == MigrationState.MIGRATION_REQUIRED:
            migration_action = "Migration and finalization needed"
        elif stats["status"] == MigrationState.FINALIZATION_REQUIRED:
            migration_action = "Finalization needed"
        self.logger.info(
            dedent(
                f"""\
            - Registered migrations for migration index {self.target_migration_index}
            - Datastore has {stats['positions']} positions with {stats['events']} events
            - The positions have a migration index of {stats['current_migration_index']}
            -> {action}
            - There are {stats['fully_migrated_positions']} fully migrated positions and
            {stats['partially_migrated_positions']} partially migrated ones
            -> {migration_action}
            - {stats['positions'] - stats['fully_migrated_positions']} positions have to be migrated (including
            partially migrated ones)\
            """
            )
        )

    def assert_valid_migration_index(self, curs: Cursor[DictRow]) -> None:
        """assert consistent migration index"""
        database_m_idx = MigrationHelper.get_database_migration_index(self.cursor)
        if database_m_idx > self.target_migration_index:
            raise MismatchingMigrationIndicesException(
                "The database has a higher migration index "
                + f"({database_m_idx}) than the registered"
                + f" migrations ({self.target_migration_index})"
            )
        if self.verbose:
            self.logger.info(f"Current migration index: {database_m_idx}")

    def handle_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not (command := payload.get("cmd")):
            raise View400Exception("No command provided")
        self.logger.info(f"Migration command: {command}")
        with get_new_os_conn() as conn:
            conn.transaction()
            with conn.cursor() as curs:
                self.cursor = curs
                if command == MigrationCommand.PROGRESS:
                    return self.handle_progress_command()
                if command == "stats":
                    return {"stats": self.get_stats()}
                self.assert_valid_migration_index(curs)

                if (
                    MigrationHelper.get_migration_state(curs)
                    == MigrationState.MIGRATION_RUNNING
                ):
                    raise View400Exception(
                        "Migration is running, only 'stats' command is allowed."
                    )

                if MigrationHelper.migrate_thread_stream:
                    if MigrationHelper.migrate_thread_stream_can_be_closed:
                        MigrationHandler.close_migrate_thread_stream()
                    else:
                        raise View400Exception(
                            "Last migration output not read yet. Please call 'progress' first."
                        )

                verbose = payload.get("verbose", False)
                if command in iter(MigrationCommand):
                    MigrationHelper.migrate_thread_stream = StringIO()
                    thread = Thread(
                        target=self.execute_migrate_command, args=[command, verbose]
                    )
                    thread.start()
                    thread.join(THREAD_WAIT_TIME)
                    if thread.is_alive():
                        # Migration still running. Report current progress and return
                        return {
                            "status": MigrationState.MIGRATION_RUNNING,
                            "output": MigrationHelper.migrate_thread_stream.getvalue(),
                        }
                    else:
                        # Migration already finished/had nothing to do
                        return MigrationHelper.get_migration_result(curs)
                else:
                    raise View400Exception("Unknown command: " + command)

    def execute_migrate_command(self, command: str, verbose: bool) -> None:
        """
        Should be called as a new Thread.
        Should only be called if migration is in a correct state. Error handling in this is minimalistic.
        """
        try:
            with get_new_os_conn() as conn:
                with conn.cursor() as curs:
                    if (
                        MigrationHelper.get_migration_state(curs)
                        == MigrationState.MIGRATION_RUNNING
                        and command != MigrationCommand.RESET
                    ):
                        raise MigrationException(
                            f"Cannot {command} when migration is running."
                        )

                    self.handler = MigrationHandler(
                        curs, self.env, self.services, self.logging
                    )
                    return self.handler.execute_command(command)
        except Exception as e:
            MigrationHelper.migrate_thread_exception = e
            self.logger.exception(e)
