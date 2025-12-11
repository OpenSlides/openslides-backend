from importlib import import_module
from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from ..migrations.core.exceptions import InvalidMigrationCommand, MigrationException
from ..migrations.migration_helper import (
    LAST_NON_REL_MIGRATION,
    MODULE_PATH,
    MigrationHelper,
    MigrationState,
)
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

    def set_migration_relations(self) -> None:
        """Sets the tables and views used within the migration."""
        unified_replace_tables, _ = (
            MigrationHelper.get_unified_replace_tables_from_database(self.cursor)
        )
        for collection, m_data in unified_replace_tables.items():
            self.cursor.execute(
                sql.SQL(
                    "CREATE TABLE {table_m} (LIKE {table_t} INCLUDING ALL);"
                ).format(
                    table_m=sql.Identifier(m_data["table"]),
                    table_t=sql.Identifier(collection + "_t"),
                )
            )
            self.cursor.execute(
                sql.SQL("CREATE VIEW {view_m} (LIKE {view} INCLUDING ALL);").format(
                    view_m=sql.Identifier(m_data["view"]),
                    view=sql.Identifier(collection),
                )
            )

    def execute_migrations(self) -> None:
        """
        Executes the data_definition and data_manipulation methods of the migrations
        stored in MigrationHelper.migrations.

        Returns:
        - None
        """
        module_name: str

        for index, migration in MigrationHelper.migrations.items():
            module_name = migration
            migration_module = import_module(f"{MODULE_PATH}{module_name}")
            current_mi = MigrationHelper.get_database_migration_index(self.cursor)
            if not current_mi == LAST_NON_REL_MIGRATION:
                self.set_migration_relations()
            print("Executing migration: " + module_name)
            if getattr(migration_module, "IN_MEMORY", False):
                # TODO In-Memory migration
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

                MigrationHelper.set_database_migration_info(
                    self.cursor, index, MigrationState.FINALIZATION_REQUIRED
                )

    def migrate(self) -> None:
        """
        Starts the migration process.
        """
        self.logger.info("Running migrations.")
        state = MigrationHelper.get_migration_state(self.cursor)
        match state:
            case MigrationState.MIGRATION_REQUIRED:
                self.execute_migrations()
                MigrationHelper.migrate_thread_stream_can_be_closed = True
                MigrationHelper.write_line("finished")
            case MigrationState.FINALIZATION_REQUIRED:
                self.logger.info("Done. Finalizing is still needed.")
            case MigrationState.FINALIZED:
                self.logger.info("No migration needed.")
            case MigrationState.MIGRATION_RUNNING:
                self.logger.info("There is already a migration running.")
            case _:
                raise MigrationException(
                    f"{state} not allowed when executing migrate command."
                )

    def execute_command(self, command: str) -> None:
        """
        Low level entry point.
        """
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

    # TODO affected tables to read only plus this information to version table -> needs to store collections and trigger names in migration manager
    # CREATE OR REPLACE FUNCTION prevent_writes() RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'Table % is currently read-only', TG_TABLE_NAME; END; $$ LANGUAGE plpgsql;
    # CREATE TRIGGER block_writes BEFORE INSERT OR UPDATE OR DELETE ON your_schema.your_table FOR EACH STATEMENT EXECUTE FUNCTION prevent_writes();
    # To remove later: DROP TRIGGER block_writes ON your_schema.your_table; DROP FUNCTION prevent_writes();

    # or simply REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE your_schema.your_table FROM PUBLIC;

    # which option needs transaction monitioring before migration can start?
    # SELECT pid, usename, application_name, client_addr, state, backend_xid, query FROM pg_stat_activity WHERE datname = current_database();

    @classmethod
    def close_migrate_thread_stream(cls) -> str:
        """
        Closes the migration threads io stream.
        """
        assert (stream := MigrationHelper.migrate_thread_stream)
        output = stream.getvalue()
        stream.close()
        MigrationHelper.migrate_thread_stream = None
        MigrationHelper.migrate_thread_stream_can_be_closed = False
        MigrationHelper.migrate_thread_exception = None
        return output

    def finalize(self) -> None:
        """
        Executes the cleanup method and copies tables into place.
        Also sets the migration index correctly.
        """
        state = MigrationHelper.get_migration_state(self.cursor)
        match state:
            case MigrationState.FINALIZED:
                return
            case MigrationState.MIGRATION_REQUIRED:
                self.migrate()
                return self.finalize()
            case MigrationState.FINALIZATION_REQUIRED:
                # TODO do we need to set a new state FINALIZATION_RUNNING?
                self.logger.info("Finalize migrations.")
            case _:
                raise MigrationException(
                    f"State is: {state} Finalization not possible if it's not required."
                )

        for index, migration in MigrationHelper.migrations.items():
            module_name = migration
            migration_module = import_module(f"{MODULE_PATH}{module_name}")
            if callable(getattr(migration_module, "cleanup", None)):
                migration_module.cleanup(self.cursor)

        # current_mi = MigrationHelper.get_database_migration_index(self.cursor)
        # relevant_mis = [
        #     mi
        #     for mi in MigrationHelper.get_indices_from_database(self.cursor)
        #     if mi > current_mi
        # ]
        # replace_tables = {
        #     collection: shadows
        #     for migration_number in relevant_mis
        #     for collection, shadows in MigrationHelper.get_replace_tables_from_database(
        #         self.cursor, migration_number
        #     ).items()
        # }
        unified_replace_tables, relevant_mis = (
            MigrationHelper.get_unified_replace_tables_from_database(self.cursor)
        )
        for collection, shadow_names in unified_replace_tables.items():
            # TODO automatism to redo the constraints trigger etc before and after copying the table contents.
            self.cursor.execute(
                sql.SQL("DROP TABLE {real_name}").format(
                    real_name=sql.Identifier(collection + "_t")
                )
            )
            self.cursor.execute(
                ("ALTER TABLE {shadow_name} RENAME TO {real_name}").format(
                    real_name=sql.Identifier(collection + "_t"),
                    shadow_name=sql.Identifier(shadow_names["table"]),
                )
            )
            self.cursor.execute(
                sql.SQL("DROP VIEW {real_name}").format(
                    real_name=sql.Identifier(collection)
                )
            )
            self.cursor.execute(
                ("ALTER VIEW {shadow_name} RENAME TO {real_name}").format(
                    real_name=sql.Identifier(collection),
                    shadow_name=sql.Identifier(shadow_names["view"]),
                )
            )
        for mi in relevant_mis:
            MigrationHelper.set_database_migration_info(
                self.cursor, mi, MigrationState.FINALIZED
            )
        self.logger.info(f"Set the new migration index to {max(relevant_mis)}...")

    def reset(self) -> None:
        """
        Resets the migrations currently in progress and restores the state before the migration.
        """
        self.logger.info("Reset migrations.")
        self.close_migrate_thread_stream()
        self._clean_migration_data()
        indices = MigrationHelper.get_indices_from_database(self.cursor)
        to_delete_indices = [
            idx
            for idx, state in MigrationHelper.get_database_migration_states(
                self.cursor, indices
            ).items()
            if state != MigrationState.FINALIZED
        ]
        self.cursor.execute(
            sql.SQL("DELETE from version WHERE migration_index = ANY(")
            + sql.Placeholder()
            + sql.SQL(");"),
            (to_delete_indices,),
        )

    def _clean_migration_data(self) -> None:
        self.logger.info("Clean up migration data...")
        assert self.cursor, "Handlers cursor must be initialized."
        indices = MigrationHelper.get_indices_from_database(self.cursor)
        state_per_idx = MigrationHelper.get_database_migration_states(
            self.cursor, indices
        )
        replace_tables = {
            k: v
            for idx, state in state_per_idx.items()
            if state != MigrationState.FINALIZED
            for k, v in MigrationHelper.get_replace_tables(idx).items()
        }
        for table_view in replace_tables.values():
            self.cursor.execute(f"DROP TABLE {table_view['table']}")
            self.cursor.execute(f"DROP VIEW {table_view['view']}")

    # TODO delete shadow copies and as other possibly necessary alterations
    #     self.cursor.execute("delete from migration_positions", [])
    #     self.cursor.execute("delete from migration_events", [])
    #     sequence = self.cursor.execute(
    #         "select pg_get_serial_sequence('migration_events', 'id');", []
    #     ).fetchone()
    #     self.cursor.execute(f"alter sequence {sequence} restart with 1", [])
