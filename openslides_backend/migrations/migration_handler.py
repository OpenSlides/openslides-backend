import os
from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.migration_helper import (
    MIGRATIONS_PATH,
    MigrationHelper,
    MigrationState,
)
from openslides_backend.services.postgresql.utils import (
    activate_notify_triggers,
    deactivate_notify_triggers,
)

from ..migrations.exceptions import (
    InvalidMigrationCommand,
    MigrationException,
    MigrationSetupException,
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
        version_connection: Any,
    ) -> None:
        super().__init__(env, services, logging)
        self.migration_cursor = curs
        self.ver_conn = version_connection
        self.replace_tables: dict[str, Any]

    def update_sequence(self, name: str, maximum: int) -> None:
        self.migration_cursor.execute(
            sql.SQL("SELECT setval('{sequence_name}', {maximum});").format(
                sequence_name=sql.SQL(name),
                maximum=maximum,
            )
        )

    def update_sequences(self) -> None:
        """
        Updates all primary keys.
        """
        with self.ver_conn.cursor() as ver_cursor:
            unified_repl_tables = (
                MigrationHelper.get_unified_replace_tables_from_database(ver_cursor)
            )
        for collection in unified_repl_tables:
            table_name = HelperGetNames.get_table_name(collection)
            table = sql.Identifier(table_name)
            # update primary keys.
            result = self.migration_cursor.execute(
                sql.SQL("SELECT MAX(id) FROM {table_name};").format(table_name=table)
            ).fetchone()
            if result:
                self.update_sequence(
                    table_name + "_id_seq",
                    result["max"],
                )

    def apply_schema_diff(self, migration_number: int) -> None:
        """Applies the sql diff for the given migration if it exists."""
        try:
            with open(
                os.path.join(
                    MIGRATIONS_PATH,
                    MigrationHelper.migrations[migration_number],
                    "schema_diff.sql",
                )
            ) as f:
                self.migration_cursor.execute(f.read())
        except FileNotFoundError:
            self.logger.warning(
                f"Couldn't find an SQL diff for {migration_number}. This can be intentional."
            )
        except Exception as e:
            raise MigrationException(f"Error applying schema diff: {e}")

    def execute_migrations(self) -> None:
        """
        Executes the data_definition and data_manipulation methods of the migrations
        stored in MigrationHelper.migrations.
        """
        for index, package_name in MigrationHelper.migrations.items():
            try:
                mig_class = MigrationHelper.get_migration_class(package_name)
                self.logger.info("Executing migration: " + package_name)

                self.apply_schema_diff(index)
                # Execute user defined functions or super classes noop.
                stash = mig_class.data_preparation(self.migration_cursor)
                mig_class.data_definition(self.migration_cursor)
                mig_class.data_manipulation(self.migration_cursor, stash)
                mig_class.cleanup(self.migration_cursor)

                with self.ver_conn.cursor() as ver_curs:
                    MigrationHelper.set_database_migration_info(
                        ver_curs, index, MigrationState.MIGRATION_FINISHED
                    )
            except Exception as e:
                MigrationHelper.migrate_thread_exception = e
                with self.ver_conn.cursor() as ver_curs:
                    MigrationHelper.set_database_migration_info(
                        ver_curs, index, MigrationState.MIGRATION_FAILED
                    )
                raise e

        # Needs to happen before sequence update because the latter circumvents transaction logic.
        self.migration_cursor.connection.commit()
        # This could theoretically set the sequences to values we don't want because this circumvents transaction logic
        self.update_sequences()
        with self.ver_conn.cursor() as ver_curs:
            for migration_number in MigrationHelper.migrations:
                MigrationHelper.set_database_migration_info(
                    self.migration_cursor, migration_number, MigrationState.FINALIZED
                )
        self.logger.info(
            f"Migration index was set to {max(MigrationHelper.migrations)}..."
        )

    def migrate(self) -> None:
        """
        Starts the migration process.
        """
        self.logger.info("Checking migratability ...")
        with self.ver_conn.cursor() as ver_cursor:
            state = MigrationHelper.get_migration_state(ver_cursor)
            match state:
                case MigrationState.MIGRATION_REQUIRED:
                    # Block other migration requests by setting state to preparing.
                    if minimum_required_index := ver_cursor.execute(
                        sql.SQL(
                            "SELECT MIN(migration_index) FROM version WHERE migration_state = %s"
                        ),
                        (MigrationState.MIGRATION_REQUIRED,),
                    ).fetchone():
                        MigrationHelper.set_database_migration_info(
                            ver_cursor,
                            minimum_required_index["min"],
                            MigrationState.MIGRATION_RUNNING,
                        )
                    # Check prerequisites
                    for index, package_name in MigrationHelper.migrations.items():
                        mig_class = MigrationHelper.get_migration_class(package_name)
                        mig_name = package_name[4:]
                        self.logger.info("Pre check: " + mig_name + " ...")
                        if errors := mig_class.check_prerequisites(
                            self.migration_cursor
                        ):
                            if minimum_required_index:
                                MigrationHelper.set_database_migration_info(
                                    ver_cursor,
                                    minimum_required_index["min"],
                                    MigrationState.MIGRATION_REQUIRED,
                                )
                            errors = (
                                f"Pre check for migration {mig_name} failed.\n{errors}"
                            )
                            self.logger.info(errors)
                            raise MigrationSetupException(errors)
                    MigrationHelper.write_line("migration started")
                    deactivate_notify_triggers(self.migration_cursor)
                    self.execute_migrations()
                    activate_notify_triggers(self.migration_cursor)
                    MigrationHelper.write_line("migration finished")
                    MigrationHelper.migrate_thread_stream_can_be_closed = True
                case MigrationState.MIGRATION_FINISHED:
                    self.logger.info("Done. About to finish.")
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
            self.migration_cursor and not self.migration_cursor.closed
        ), "Handlers cursor must be initialized."
        if command == "migrate":
            self.migrate()
        elif command == "reset":
            self.reset()
        else:
            raise InvalidMigrationCommand(command)

    def reset(self) -> None:
        """
        Resets the migrations currently in progress and restores the state before the migration.
        """
        self.logger.info("Reset migrations.")
        MigrationHelper.close_migrate_thread_stream()
        MigrationHelper.migrate_thread_exception = None
        # Remove unfinalized migration indices from version table
        with self.ver_conn.cursor() as ver_cursor:
            to_reset_indices = MigrationHelper.get_unfinalized_indices(ver_cursor)
            ver_cursor.execute(
                sql.SQL(
                    "UPDATE version SET migration_state = %s "
                    "WHERE migration_index = ANY(%s)"
                ),
                (MigrationState.MIGRATION_REQUIRED, to_reset_indices),
            )
