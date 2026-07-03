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
from openslides_backend.shared.exceptions import CommandNotImplemented

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
        self.cursor = curs
        self.replace_tables: dict[str, Any]

    # TODO This might still be relevant inside the module code for stowing away information dropped by schema alterations
    # def copy_table(self, table_name: str, target_table_name: str) -> None:
    #     """Copies the table with its definition and rows. Does not copy trigger."""
    #     target_table = sql.Identifier(target_table_name)
    #     table_t = sql.Identifier(table_name)
    #     self.cursor.execute(
    #         sql.SQL("CREATE TABLE {target_table} (LIKE {table_t} INCLUDING ALL);").format(
    #             target_table=target_table, table_t=table_t
    #         )
    #     )

    #     fields = self.cursor.execute(sql.SQL("""
    #             SELECT *
    #             FROM information_schema.columns
    #             WHERE table_schema = 'public'
    #             AND table_name = {table};
    #             """).format(table=table_name)).fetchall()
    #     self.cursor.execute(
    #         sql.SQL(
    #             "INSERT INTO {target_table} ({fields}) SELECT {fields} FROM {table_t};"
    #         ).format(
    #             target_table=target_table,
    #             table_t=table_t,
    #             fields=sql.SQL(", ").join(
    #                 sql.SQL(data["column_name"])
    #                 for data in fields
    #                 if data["is_generated"] != "ALWAYS"
    #             ),
    #         )
    #     )

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
                    MigrationHelper.migrations[migration_number],
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
        stored in MigrationHelper.migrations.
        """
        for index, package_name in MigrationHelper.migrations.items():
            mig_class = MigrationHelper.get_migration_class(package_name)
            self.logger.info("Executing migration: " + package_name)

            self.apply_schema_diff(index)
            # Execute user defined functions or super classes noop.
            mig_class.data_definition(self.cursor)
            mig_class.data_manipulation(self.cursor)
            mig_class.cleanup(self.cursor)

            MigrationHelper.set_database_migration_info(
                self.cursor, index, MigrationState.MIGRATION_FINISHED
            )

        # This could theoretically set the sequences to values we don't want because this circumvents transaction logic
        self.update_sequences()
        for migration_number in MigrationHelper.migrations:
            MigrationHelper.set_database_migration_info(
                self.cursor, migration_number, MigrationState.FINALIZED
            )
        self.logger.info(
            f"Migration index was set to {max(MigrationHelper.migrations)}..."
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
                for index, package_name in MigrationHelper.migrations.items():
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
                # self.set_public_tables_read_only()
                # self.setup_migration_relations()
                self.execute_migrations()
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
        raise CommandNotImplemented("The reset route is not implemented yet.")
        self.logger.info("Reset migrations.")
        MigrationHelper.close_migrate_thread_stream()
        self._clean_migration_data()
        indices = MigrationHelper.get_indices_from_database(self.cursor)
        # Remove unfinalized migration indices from version table
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

        self.unset_tables_read_only()

    def _clean_migration_data(self) -> None:
        """
        Removes migration tables and views
        """
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
            for k, v in MigrationHelper.get_replace_tables_from_database(
                self.cursor, idx
            ).items()
        }
        for collection in replace_tables:
            self.cursor.execute(f"DROP TABLE {collection}_m;")
        if any(mi > 100 for mi in indices):
            for table_view in replace_tables.values():
                self.cursor.execute(f"DROP TABLE {table_view['table']};")
                self.cursor.execute(f"DROP VIEW {table_view['view']};")
