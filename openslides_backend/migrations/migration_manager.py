from collections.abc import Callable
from io import StringIO
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
        """
        # TODO delete once tooling will handle the stats route instead.
        """
        return self.get_migration_result()

    def get_migration_result(self) -> dict[str, Any]:
        """
        Closes the migration threads io stream.
        """
        state = MigrationHelper.get_migration_state(self.cursor)
        result = {"status": str(state)}
        if MigrationHelper.migrate_thread_stream and (
            output := MigrationHelper.migrate_thread_stream.getvalue()
        ):
            # The last line (index -1) will always be an empty string.
            last_line = output.split("\n")[-2]
            MigrationHelper.write_line(last_line)
            result["output"] = f"{last_line}\n"
        if MigrationHelper.migrate_thread_exception:
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

        def count(table: str, curs: Cursor[DictRow]) -> int:
            if current_migration_index == LAST_NON_REL_MIGRATION:
                if table.endswith("_m"):
                    # initial migration uses the original table_t instead of shadow table_m
                    # to count migrated models.
                    statement_part = sql.SQL("{table}").format(
                        table=sql.Identifier(table[:-2] + "_t")
                    )
                else:
                    # initial migration uses the models instead of table_t to count models
                    statement_part = sql.SQL(
                        "models WHERE fqid LIKE '{collection}/%' and deleted = false"
                    ).format(collection=sql.SQL(table[:-2]))
            else:
                statement_part = sql.SQL("{table}").format(table=sql.Identifier(table))
            response = self.cursor.execute(
                sql.SQL("SELECT COUNT(*) FROM ") + statement_part
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
            collection: shadow["table"]
            for mi in migration_indices
            if mi > current_migration_index
            if state_per_mi[mi]
            in (MigrationState.MIGRATION_REQUIRED, MigrationState.MIGRATION_RUNNING)
            for collection, shadow in MigrationHelper.get_replace_tables(mi).items()
        }
        stats = {
            collection: {
                "count": amount,
                "migrated": count(migration_table, self.cursor),
            }
            for collection, migration_table in unmigrated_collections.items()
            if (amount := count(collection + "_t", self.cursor))
        }

        return {
            **self.get_migration_result(),
            "current_migration_index": current_migration_index,
            "target_migration_index": self.target_migration_index,
            "migratable_models": stats,
            **(
                {"exception": MigrationHelper.migrate_thread_exception}
                if MigrationHelper.migrate_thread_exception
                else {}
            ),
        }

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
        """
        Entry point for the migrate route.
        Will start a new migration thread if it is required and requested.
        """
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

                state = MigrationHelper.get_migration_state(curs)
                if state == MigrationState.MIGRATION_RUNNING:
                    raise View400Exception(
                        "Migration is running, only 'stats' command is allowed."
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
                        return self.get_migration_result()
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
