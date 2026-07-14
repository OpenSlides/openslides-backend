import os

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.migration_helper import (
    MIGRATIONS_PATH,
    MigrationHelper,
    MigrationState,
)
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
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
    ) -> None:
        super().__init__(env, services, logging)
        database_m_idx = MigrationHelper.get_database_migration_index(curs)
        self.cursor = curs
        self.pending_migrations = {
            mig: directory
            for mig, directory in MigrationHelper.migrations.items()
            if mig > database_m_idx
        }

    def update_sequence(self, name: str, maximum: int) -> None:
        self.cursor.execute(
            sql.SQL("SELECT setval('{sequence_name}', {maximum});").format(
                sequence_name=sql.SQL(name),
                maximum=maximum,
            )
        )

    def update_sequences(self) -> None:
        """
        Updates all primary keys and sequential_number fields.
        """
        unified_repl_tables = MigrationHelper.get_unified_replace_tables_from_database(
            self.cursor
        )
        for collection in unified_repl_tables:
            table_name = HelperGetNames.get_table_name(collection)
            table = sql.Identifier(table_name)
            # update primary keys.
            result = self.cursor.execute(
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
                    self.pending_migrations[migration_number],
                    "schema_diff.sql",
                )
            ) as f:
                self.cursor.execute(f.read())
        except FileNotFoundError:
            self.logger.warning(
                f"Couldn't find an SQL diff for {migration_number}. This can be intentional."
            )
        except Exception as e:
            raise MigrationException(f"Error applying schema diff: {e}")

    def execute_migrations(self) -> None:
        """
        Executes the data_definition and data_manipulation methods of the migrations
        stored in self.pending_migrations.
        """
        for index, package_name in self.pending_migrations.items():
            try:
                mig_class = MigrationHelper.get_migration_class(package_name)
                self.logger.info("Executing migration: " + package_name)

                self.apply_schema_diff(index)
                # Execute user defined functions or super classes noop.
                stash = mig_class.data_preparation(self.cursor)
                mig_class.data_definition(self.cursor)
                mig_class.data_manipulation(self.cursor, stash)
                mig_class.cleanup(self.cursor)

                MigrationHelper.set_database_migration_info(
                    self.cursor, index, MigrationState.MIGRATION_FINISHED
                )
            except Exception as e:
                # TODO needs to be the ver_conn
                MigrationHelper.migrate_thread_exception = e
                with get_new_os_conn() as conn:
                    with conn.cursor() as curs:
                        MigrationHelper.set_database_migration_info(
                            curs, index, MigrationState.MIGRATION_FAILED
                        )
                raise e

        # This could theoretically set the sequences to values we don't want because this circumvents transaction logic
        self.update_sequences()
        for migration_number in self.pending_migrations:
            MigrationHelper.set_database_migration_info(
                self.cursor, migration_number, MigrationState.FINALIZED
            )
        self.logger.info(
            f"Migration index was set to {max(self.pending_migrations)}..."
        )

    def migrate(self) -> None:
        """
        Starts the migration process.
        """
        self.logger.info("Checking migratability ...")
        state = MigrationHelper.get_migration_state(self.cursor)
        match state:
            case MigrationState.MIGRATION_REQUIRED:
                # Block other migration requests by setting state to preparing.
                if minimum_required_index := self.cursor.execute(
                    sql.SQL(
                        "SELECT MIN(migration_index) FROM version WHERE migration_state = %s"
                    ),
                    (MigrationState.MIGRATION_REQUIRED,),
                ).fetchone():
                    MigrationHelper.set_database_migration_info(
                        self.cursor,
                        minimum_required_index["min"],
                        MigrationState.MIGRATION_RUNNING,
                    )
                # Check prerequisites
                for index, package_name in self.pending_migrations.items():
                    mig_class = MigrationHelper.get_migration_class(package_name)
                    mig_name = package_name[4:]
                    self.logger.info("Pre check: " + mig_name + " ...")
                    if errors := mig_class.check_prerequisites(self.cursor):
                        if minimum_required_index:
                            MigrationHelper.set_database_migration_info(
                                self.cursor,
                                minimum_required_index["min"],
                                MigrationState.MIGRATION_REQUIRED,
                            )
                        errors = f"Pre check for migration {mig_name} failed.\n{errors}"
                        self.logger.info(errors)
                        raise MigrationSetupException(errors)
                MigrationHelper.write_line("migration started")
                deactivate_notify_triggers(self.cursor)
                self.execute_migrations()
                activate_notify_triggers(self.cursor)
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
            self.cursor and not self.cursor.closed
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
        activate_notify_triggers(self.cursor)
        MigrationHelper.close_migrate_thread_stream()
        MigrationHelper.migrate_thread_exception = None
        # Remove unfinalized migration indices from version table
        to_reset_indices = MigrationHelper.get_unfinalized_indices(self.cursor)
        self.cursor.execute(
            sql.SQL(
                "UPDATE version SET migration_state = %s "
                "WHERE migration_index = ANY(%s)"
            ),
            (MigrationState.MIGRATION_REQUIRED, to_reset_indices),
        )
