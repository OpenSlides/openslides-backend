from collections.abc import Callable
from io import StringIO
from threading import Thread
from typing import Any, cast

from psycopg import sql

from openslides_backend.migrations.exceptions import (
    MigrationException,
    MigrationSetupException,
    MismatchingMigrationIndicesException,
)
from openslides_backend.migrations.migration_helper import (
    MIN_NON_REL_MIGRATION,
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
        """Also updates the version table with new migrations"""
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
        """
        Returns an intermediate result of the running migration, reading all
        new output written since the last regular read (i.e. since last
        progress call).
        """
        return self.get_migration_result()

    def get_migration_result(self, all: bool = False) -> dict[str, Any]:
        """
        Gets the 'status' and migration threads 'output' string. 'exception' if
        an exception occured.
        """
        state = MigrationHelper.get_migration_state(self.cursor)
        result = {"status": str(state), "output": ""}

        if MigrationHelper.migrate_thread_stream:
            result["output"] = MigrationHelper.read_stream(all)

        if state in (
            MigrationState.MIGRATION_FAILED,
            MigrationState.FINALIZATION_FAILED,
        ):
            result["exception"] = str(MigrationHelper.migrate_thread_exception)

        return result

    def get_stats(self) -> dict[str, Any]:
        """
        Gets the following stats:
        status: The current overall state.
        current_migration_index: The current migration index.
        target_migration_index: The current backend index that is targeted by the migrations.
        migratable_models: Rough amounts per collection to be migrated.
            Doesn't respect initial migration if executed on a higher target migration index.
        """

        def count(table: str) -> int:
            if MIN_NON_REL_MIGRATION <= current_migration_index < 100:
                # initial migration uses the models instead of table_t to count models
                statement_part = sql.SQL(
                    "models WHERE fqid LIKE '{collection}/%' and deleted = false"
                ).format(collection=sql.SQL(table[:-2]))
            else:
                statement_part = sql.SQL("{table}").format(table=sql.Identifier(table))
            response = self.cursor.execute(
                sql.SQL("SELECT COUNT(*) FROM ") + statement_part
            ).fetchone()
            return (response or {}).get("count", 0)

        current_migration_index = MigrationHelper.get_database_migration_index(
            self.cursor
        )

        if not MigrationHelper.migrate_thread_exception:
            migration_indices = MigrationHelper.get_indices_from_database(self.cursor)
            state_per_mi = MigrationHelper.get_database_migration_states(
                self.cursor, migration_indices
            )
            unmigrated_collections = {
                collection: cast(str, r_tables["table"])
                for mi in migration_indices
                if mi > current_migration_index
                if state_per_mi[mi]
                in (
                    MigrationState.MIGRATION_REQUIRED,
                    MigrationState.MIGRATION_RUNNING,
                )
                for collection, r_tables in MigrationHelper.get_replace_tables(
                    mi
                ).items()
            }
            stats = {
                collection: amount
                for collection, migration_table in unmigrated_collections.items()
                if (amount := count(collection + "_t"))
            }

        if exc := MigrationHelper.migrate_thread_exception:
            module_name = getattr(exc, "__module__", "")
        return {
            # stats returns all output without disturbing concurrent progress calls
            # -> all=True
            **self.get_migration_result(all=True),
            "current_migration_index": current_migration_index,
            "target_migration_index": self.target_migration_index,
            **(
                {
                    "exception": f"{module_name}{'.' if module_name else ''}{type(exc).__qualname__}: {exc}"
                }
                if exc
                else {"migratable_models": stats}
            ),
        }

    def assert_valid_migration_index(self) -> None:
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
        """
        Entry point for the migrate route.
        Will start a new migration thread if it is required and requested.
        """
        if not (command := payload.get("cmd")):
            raise View400Exception("No command provided")
        self.logger.info(f"Migration command: {command}")
        if command not in iter(MigrationCommand):
            raise View400Exception("Unknown command: " + command)
        with get_new_os_conn() as conn:
            conn.transaction()
            with conn.cursor() as curs:
                self.cursor = curs
                state = MigrationHelper.get_migration_state(curs)
                if command == MigrationCommand.PROGRESS:
                    return self.handle_progress_command()
                elif command == MigrationCommand.STATS:
                    return {"stats": self.get_stats()}
                elif command != MigrationCommand.RESET:
                    self.assert_valid_migration_index()

                    match state:
                        case MigrationState.MIGRATION_RUNNING:
                            process = "Migration"
                        case MigrationState.FINALIZATION_RUNNING:
                            process = "Finalization"
                        case (
                            MigrationState.MIGRATION_FAILED
                            | MigrationState.FINALIZATION_FAILED
                        ):
                            raise MigrationException(
                                f"Migration in a failed state. Reset before trying to {command} again. Failed on: {MigrationHelper.migrate_thread_exception}"
                            )
                        case _:
                            process = ""
                    if process:
                        raise MigrationException(
                            f"{process} is running, only 'stats' command is allowed."
                        )

                verbose = payload.get("verbose", False)
                MigrationHelper.migrate_thread_stream = StringIO()
                MigrationHelper.migrate_thread_stream_read_pos = (
                    MigrationHelper.migrate_thread_stream.tell()
                )
                MigrationHelper.migrate_thread = thread = Thread(
                    target=self.execute_migrate_command, args=[command, verbose]
                )
                thread.start()
                thread.join(THREAD_WAIT_TIME)
                if thread.is_alive():
                    # Read isolation would prevent seeing the newest status otherwise.
                    self.cursor.connection.commit()
                    # Migration still running. Report current progress and return
                    return {
                        "status": MigrationHelper.get_migration_state(self.cursor),
                        "output": MigrationHelper.read_stream(),
                    }
                else:
                    # Migration already finished/had nothing to do
                    return self.get_migration_result()

    def execute_migrate_command(self, command: str, verbose: bool) -> None:
        """
        Should be called as a new Thread.
        Should only be called if migration is in a correct state. Error handling in this is minimalistic.
        If an exception occurs during execution for the first time,
        it is stored in the MigrationHelper.migrate_thread_exception for read with MigrationCommand.STATS.
        """
        try:
            with get_new_os_conn() as conn:
                with conn.cursor() as curs:
                    state = MigrationHelper.get_migration_state(curs)
            if (
                state == MigrationState.MIGRATION_REQUIRED
                and command == MigrationCommand.FINALIZE
            ):
                self.execute_migrate_command(MigrationCommand.MIGRATE, verbose)

            with get_new_os_conn() as conn:
                with conn.cursor() as curs:
                    self.handler = MigrationHandler(
                        curs, self.env, self.services, self.logging
                    )
                    return self.handler.execute_command(command)
        except MigrationSetupException as e:
            MigrationHelper.migrate_thread_exception = e
            self.logger.exception(e)
        except Exception as e:
            # TODO catch this on a lower level and set it for specific faulty migration index
            self.logger.exception(e)
            if not MigrationHelper.migrate_thread_exception:
                MigrationHelper.migrate_thread_exception = e
                with get_new_os_conn() as conn:
                    with conn.cursor() as curs:
                        relevant_mis = MigrationHelper.get_unfinalized_indices(curs)
                        match command:
                            case MigrationCommand.MIGRATE:
                                state = MigrationState.MIGRATION_FAILED
                            case MigrationCommand.FINALIZE:
                                state = MigrationState.FINALIZATION_FAILED
                        for mi in relevant_mis:
                            MigrationHelper.set_database_migration_info(curs, mi, state)
