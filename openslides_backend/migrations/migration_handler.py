from importlib import import_module
from typing import Any

from psycopg import Cursor
from psycopg.rows import DictRow

from ..migrations.core.exceptions import InvalidMigrationCommand, MigrationException
from ..migrations.migration_helper import MODULE_PATH, MigrationHelper, MigrationState
from ..shared.handlers.base_handler import BaseHandler
from ..shared.interfaces.env import Env
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services


class MigrationHandler(BaseHandler):

    def __init__(
        self,
        curs: Cursor[DictRow],
        env: Env,
        services: Services,
        logging: LoggingModule,
    ) -> None:
        super().__init__(env, services, logging)
        self.cursor = curs
        self.replace_tables: dict[str, Any]

    def execute_migrations(self) -> None:
        """
        Executes the migrations stored in MigrationHelper.migrations.
        Every migration could provide all of the three methods data_definition,
        data_manipulation and cleanup.

        Returns:
        - None
        """
        module_name: str

        for index, migration in MigrationHelper.migrations.items():
            module_name = migration[:-3]  # remove .py of filename
            migration_module = import_module(f"{MODULE_PATH}{module_name}")
            print("Executing migration: " + module_name)
            if getattr(migration_module, "IN_MEMORY", False):
                migration_module.in_memory_method()
            else:
                MigrationHelper.set_database_migration_info(
                    self.cursor, index, MigrationState.MIGRATION_RUNNING
                )

                # checks wether the methods are available and executes them.
                if callable(getattr(migration_module, "data_definition", None)):
                    migration_module.data_definition(self.cursor)
                if callable(getattr(migration_module, "data_manipulation", None)):
                    migration_module.data_manipulation(self.cursor)
                if callable(getattr(migration_module, "cleanup", None)):
                    migration_module.cleanup(self.cursor)

                MigrationHelper.set_database_migration_info(
                    self.cursor, index, MigrationState.FINALIZATION_REQUIRED
                )
            # TODO In-Memory migration

    def migrate(self) -> None:
        self.logger.info("Running migrations.")
        # if self.run_checks():
        #     return
        state = MigrationHelper.get_migration_state(self.cursor)
        match state:
            case MigrationState.MIGRATION_REQUIRED:
                self.execute_migrations()
                MigrationHelper.migrate_thread_stream_can_be_closed = True
            case MigrationState.FINALIZATION_REQUIRED:
                self.logger.info("Done. Finalizing is still needed.")
            case MigrationState.NO_MIGRATION_REQUIRED:
                self.logger.info("No migration needed.")
            case _:
                # TODO wo wird das running und wo darf es?
                raise MigrationException(
                    f"{state} not allowed when executing migrate command."
                )

    def execute_command(self, command: str) -> None:
        assert (
            self.cursor and not self.cursor.closed
        ), "Handlers cursor must be initialized."
        if command == "migrate":
            self.migrate()
        elif command == "finalize":
            self.finalize()
        elif command == "reset":
            self.reset()
        else:
            raise InvalidMigrationCommand(command)

    def write_line(self, message: str) -> None:
        # TODO evalute the use of the thread stream
        assert (stream := MigrationHelper.migrate_thread_stream)
        stream.write(message + "\n")

    # TODO affected tables to read only plus this information to version table -> needs to store collections and trigger names in migration manager
    # CREATE OR REPLACE FUNCTION prevent_writes() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Table % is currently read-only', TG_TABLE_NAME; END; $$ LANGUAGE plpgsql;
    # CREATE TRIGGER block_writes BEFORE INSERT OR UPDATE OR DELETE ON your_schema.your_table FOR EACH STATEMENT EXECUTE FUNCTION prevent_writes();
    # To remove later: DROP TRIGGER block_writes ON your_schema.your_table; DROP FUNCTION prevent_writes();

    # or simply REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE your_schema.your_table FROM PUBLIC;

    # which option needs transaction monitioring before migration can start?
    # SELECT pid, usename, application_name, client_addr, state, backend_xid, query FROM pg_stat_activity WHERE datname = current_database();

    @classmethod
    def close_migrate_thread_stream(cls) -> str:
        assert (stream := MigrationHelper.migrate_thread_stream)
        output = stream.getvalue()
        stream.close()
        MigrationHelper.migrate_thread_stream = None
        MigrationHelper.migrate_thread_stream_can_be_closed = False
        MigrationHelper.migrate_thread_exception = None
        return output

    def finalize(self) -> None:
        """sets the migration index correctly and copies tables into place"""
        state = MigrationHelper.get_migration_state(self.cursor)
        match state:
            case MigrationState.NO_MIGRATION_REQUIRED:
                return
            case MigrationState.MIGRATION_REQUIRED:
                self.migrate()
                return self.finalize()
            case MigrationState.FINALIZATION_REQUIRED:
                # TODO do we need to set a new state FINALIZATION_RUNNING?
                self.logger.info("Finalize migrations.")
            case _:
                raise MigrationException(
                    "Finalization not possible if it's not required."
                )

        current_mi = MigrationHelper.get_database_migration_index(self.cursor)
        relevant_mis = [
            mi
            for mi in MigrationHelper.get_indices_from_database(self.cursor)
            if mi > current_mi
        ]
        replace_tables = {
            k: v
            for migration_number in relevant_mis
            for k, v in MigrationHelper.get_replace_tables_from_database(
                self.cursor, migration_number
            ).items()
        }
        for real_name, shadow_name in replace_tables.items():
            # TODO automatism to re-reference the constraints trigger etc when copying the tables.
            self.cursor.execute(f"DROP TABLE {real_name}")
            self.cursor.execute(f"ALTER TABLE {shadow_name} RENAME TO {real_name}")
        for mi in relevant_mis:
            MigrationHelper.set_database_migration_info(
                self.cursor, mi, MigrationState.NO_MIGRATION_REQUIRED, writable=True
            )
        self.logger.info(f"Set the new migration index to {max(relevant_mis)}...")

    def reset(self) -> None:
        # TODO implement
        self.logger.info("Reset migrations.")

        # self._delete_migration_keyframes()
        # self._clean_migration_data()

    # def _clean_migration_data(self) -> None:
    #     self.logger.info("Clean up migration data...")
    #     assert self.cursor, "Handlers cursor must be initialized."
    #     self.cursor.execute("delete from migration_positions", [])
    #     self.cursor.execute("delete from migration_events", [])
    #     sequence = self.cursor.execute(
    #         "select pg_get_serial_sequence('migration_events', 'id');", []
    #     ).fetchone()
    #     self.cursor.execute(f"alter sequence {sequence} restart with 1", [])
