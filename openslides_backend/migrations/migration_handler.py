import re
import string
from importlib import import_module
from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.generate_sql_schema import GenerateCodeBlocks, HelperGetNames
from openslides_backend.models.base import model_registry

from ..migrations.exceptions import InvalidMigrationCommand, MigrationException
from ..migrations.migration_helper import (
    MODULE_PATH,
    OLD_TABLES,
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

    def copy_table(self, table_name: str) -> None:
        """Copies the table with its definition and rows. Does not copy trigger."""
        table_m = sql.Identifier(HelperGetNames.get_table_name(table_name, True))
        table_t = sql.Identifier(table_name)
        self.cursor.execute(
            sql.SQL("CREATE TABLE {table_m} (LIKE {table_t} INCLUDING ALL);").format(
                table_m=table_m, table_t=table_t
            )
        )

        # TODO we might need finalization tables for future migrations to have active triggers on the table.

        fields = self.cursor.execute(sql.SQL("""
                SELECT *
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = {table};
                """).format(table=table_name)).fetchall()
        self.cursor.execute(
            sql.SQL(
                "INSERT INTO {table_m} ({fields}) SELECT {fields} FROM {table_t};"
            ).format(
                table_m=table_m,
                table_t=table_t,
                fields=sql.SQL(", ").join(
                    sql.SQL(data["column_name"])
                    for data in fields
                    if data["is_generated"] != "ALWAYS"
                ),
            )
        )

    def setup_migration_relations(self) -> None:
        """Sets the tables and views used within the migration and copies their data."""
        unified_replace_tables, _ = (
            MigrationHelper.get_unified_replace_tables_from_database(self.cursor)
        )
        im_tables = set()
        # COPY collection tables
        for collection, r_tables in unified_replace_tables.items():
            self.copy_table(collection + "_t")
            im_tables.update(r_tables["im_tables"])

        # COPY intermediate tables
        for table_name in im_tables:
            self.copy_table(table_name)

        # COPY fkey constraints
        for table_name in im_tables | {
            r_tables["table"] for r_tables in unified_replace_tables.values()
        }:
            self.cursor.execute(
                sql.SQL("""SELECT
                        tc.constraint_name,
                        tc.is_deferrable,
                        tc.initially_deferred,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        rc.delete_rule
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    JOIN information_schema.referential_constraints AS rc
                        ON rc.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema='public'
                        AND tc.table_name='{table_name}';""").format(
                    table_name=sql.SQL(table_name)
                )
            )
            results = self.cursor.fetchall()

            for result in results:
                if result["foreign_table_name"][:-2] in unified_replace_tables:
                    f_table_name = HelperGetNames.get_table_name(
                        result["foreign_table_name"], migration=True
                    )
                else:
                    f_table_name = result["foreign_table_name"]
                # TODO for future migrations where not all tables are affected.
                # Needs setting fkey pointing to migration and origin table correctly
                # to prevent running into those constraints (later not) being violated.
                # origin if not in replace tables
                # else migration
                self.cursor.execute(
                    # sql.SQL(
                    #     "ALTER TABLE {t_name} DROP CONSTRAINT {c_name};"
                    # ).format(
                    #     t_name=table_name,
                    #     c_name=sql.SQL(result["constraint_name"])
                    sql.SQL(
                        "ALTER TABLE {o_table} ADD CONSTRAINT {c_name} FOREIGN KEY ({o_column}) REFERENCES {f_table}({f_column}) ON DELETE {on_delete}{deferable}{initially_deferred};"
                    ).format(
                        o_table=sql.Identifier(
                            HelperGetNames.get_table_name(table_name, migration=True)
                        ),
                        f_table=sql.Identifier(f_table_name),
                        c_name=sql.SQL(result["constraint_name"].replace("_t_", "_m_")),
                        o_column=sql.SQL(result["column_name"]),
                        f_column=sql.SQL(result["foreign_column_name"]),
                        on_delete=sql.SQL(result["delete_rule"]),
                        deferable=sql.SQL(
                            " DEFERRABLE" if result["is_deferrable"] == "YES" else ""
                        ),
                        initially_deferred=sql.SQL(
                            " INITIALLY DEFERRED"
                            if result["initially_deferred"] == "YES"
                            else ""
                        ),
                    )
                )

        def replace_suffix(m: re.Match) -> str:
            base = m.group(1)
            return base + ("_m")

        # COPY views for migration reads
        for collection, r_tables in unified_replace_tables.items():
            # TODO create regex specifically for the replace tables to not change what should stay as origin table. Needed for future migrations.
            table_re = re.compile(r"\b([A-Za-z0-9_.]+)(_t)\b")

            self.cursor.execute(
                """
                SELECT pg_get_viewdef(%s::regclass, true) AS viewdef
                FROM pg_class
                WHERE relname = %s AND relkind = 'v';
                """,
                (collection, collection),
            )
            row = self.cursor.fetchone()
            if not row:
                raise ValueError(f"Source view not found: {collection}")
            viewdef = table_re.sub(replace_suffix, row["viewdef"])
            self.cursor.execute(
                sql.SQL("CREATE VIEW {view_m} AS {viewdef};").format(
                    view_m=sql.Identifier(r_tables["view"]),
                    viewdef=sql.SQL(viewdef),
                )
            )
            # TODO rereference all models pointing to or pointed from this collection including im tables
            # (not origin tables)
            # shouldn't that be done during finalize?

        # RECREATE some relevant triggers
        # May be error prone due to changing constraints
        (
            pre_code,
            table_name_code,
            view_name_code,
            alter_table_code,
            final_info_code,
            missing_handled_attributes,
            im_table_code,
            create_trigger_partitioned_sequences_code,
            create_trigger_1_1_relation_not_null_code,
            create_trigger_1_n_relation_not_null_code,
            create_trigger_n_m_relation_not_null_code,
            create_trigger_unique_ids_pair_code,
            create_trigger_notify_code,
            errors,
        ) = GenerateCodeBlocks.generate_the_code()
        sql_text = (
            create_trigger_1_1_relation_not_null_code
            + create_trigger_1_n_relation_not_null_code
            + create_trigger_n_m_relation_not_null_code
            + create_trigger_unique_ids_pair_code
        )
        # replace with the migration names before execute
        replaced_blocks = []
        trigger_re = re.compile(
            r"(CREATE\s+(?:CONSTRAINT\s+)?TRIGGER\b.*?;)", re.IGNORECASE | re.DOTALL
        )
        view_re = re.compile(r"\B'([A-Za-z0-9_.]+)'\B")

        def add_suffix(m: re.Match) -> str:
            base = m.group(1)
            if base in unified_replace_tables:
                return f"'{base}vm'"
            else:
                return f"'{base}'"

        for match in trigger_re.finditer(sql_text):
            block = match.group(0)
            if table_re.search(block):
                modified_block = table_re.sub(replace_suffix, block)
                replaced_blocks.append(view_re.sub(add_suffix, modified_block))
        sql_text = "".join(replaced_blocks)
        self.cursor.execute(sql_text)

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
        unified_repl_tables, _ = (
            MigrationHelper.get_unified_replace_tables_from_database(self.cursor)
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
            # update sequential_numbers.
            if model_registry[collection]().try_get_field("sequential_number"):
                results = self.cursor.execute(
                    sql.SQL(
                        "SELECT MAX(sequential_number), meeting_id FROM {table} GROUP BY meeting_id;"
                    ).format(table=table)
                ).fetchall()
                SEQ_NAME = string.Template(
                    table_name + "_meeting_id${meeting_id}_sequential_number_seq"
                )
                for result in results:
                    seq_name = SEQ_NAME.substitute({"meeting_id": result["meeting_id"]})
                    self.cursor.execute(
                        sql.SQL(f"CREATE SEQUENCE IF NOT EXISTS {seq_name};")
                    )
                    self.update_sequence(seq_name, result["max"])

    def execute_migrations(self) -> None:
        """
        Executes the data_definition and data_manipulation methods of the migrations
        stored in MigrationHelper.migrations.
        """
        module_name: str

        for index, migration in MigrationHelper.migrations.items():
            module_name = migration
            migration_module = import_module(f"{MODULE_PATH}{module_name}")
            self.logger.info("Executing migration: " + module_name)
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
                # Block other migration requests by setting state to running.
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
                MigrationHelper.write_line("started")
                self.set_public_tables_read_only()
                self.setup_migration_relations()
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

    def set_public_tables_read_only(self) -> None:
        """
        Sets all origin_collections tables to read only by creating a trigger that fails hard.
        In the case of the initial rel-db migration this also includes the old schema.
        """
        for table in MigrationHelper.get_public_tables(self.cursor):
            trigger_name = f"tr_lock_{table}"
            if self.cursor.execute(
                sql.SQL(
                    "SELECT 1 FROM pg_trigger WHERE tgname = {trigger_name};"
                ).format(trigger_name=trigger_name)
            ).fetchone():
                self.cursor.execute(
                    sql.SQL(
                        "CREATE TRIGGER IF NOT EXISTS {trigger_name} BEFORE INSERT OR UPDATE OR DELETE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION prevent_writes();"
                    ).format(
                        trigger_name=sql.SQL(trigger_name),
                        table=sql.Identifier(table),
                    )
                )

    def unset_tables_read_only(self) -> None:
        """Sets all origin_collections tables to readable by dropping the read-only trigger."""
        for table in MigrationHelper.get_public_tables(self.cursor):
            self.cursor.execute(
                sql.SQL("DROP TRIGGER IF EXISTS {trigger_name};").format(
                    trigger_name=sql.SQL(f"tr_lock_{table}")
                )
            )
        # Support reset on initial migration.
        if MigrationHelper.get_database_migration_index(self.cursor) < 100:
            for table in OLD_TABLES:
                self.cursor.execute(
                    sql.SQL("DROP TRIGGER IF EXISTS tr_lock_{table}").format(
                        table=sql.SQL(table)
                    )
                )

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
        Also sets the migration info accordingly.
        """
        state = MigrationHelper.get_migration_state(self.cursor)
        match state:
            case MigrationState.FINALIZED:
                return
            case MigrationState.MIGRATION_REQUIRED:
                self.migrate()
                return self.finalize()
            case MigrationState.FINALIZATION_REQUIRED:
                self.logger.info("Finalize migrations.")
            case _:
                raise MigrationException(
                    f"State is: {state} Finalization not possible if it's not required."
                )

        MigrationHelper.write_line("finalization started")
        for index, migration in MigrationHelper.migrations.items():
            module_name = migration
            migration_module = import_module(f"{MODULE_PATH}{module_name}")
            if callable(getattr(migration_module, "cleanup", None)):
                migration_module.cleanup(self.cursor)

        unified_replace_tables, relevant_mis = (
            MigrationHelper.get_unified_replace_tables_from_database(self.cursor)
        )
        for mi in relevant_mis:
            MigrationHelper.set_database_migration_info(
                self.cursor, mi, MigrationState.FINALIZATION_RUNNING
            )

        im_tables = set()
        # Do the general replacement
        for collection, migration_names in unified_replace_tables.items():
            # Will also drop attached intermediate tables and views.
            self.cursor.execute(
                sql.SQL("DROP TABLE {real_name} CASCADE;").format(
                    real_name=sql.Identifier(collection + "_t")
                )
            )
            self.cursor.execute(
                sql.SQL("ALTER TABLE {migration_name} RENAME TO {real_name}").format(
                    real_name=sql.Identifier(collection + "_t"),
                    migration_name=sql.Identifier(migration_names["table"]),
                )
            )
            self.cursor.execute(
                sql.SQL(
                    "ALTER SEQUENCE {collection}_m_id_seq RENAME TO {collection}_t_id_seq;"
                ).format(collection=sql.SQL(collection))
            )
            # Will be recreated for origin table below.
            self.cursor.execute(
                sql.SQL("DROP VIEW {migration_name};").format(
                    migration_name=sql.Identifier(migration_names["view"]),
                )
            )
            im_tables.update(migration_names["im_tables"])

        # RENAME intermediate tables
        for table_name in im_tables:
            self.cursor.execute(
                sql.SQL("DROP TABLE {real_name};").format(
                    real_name=sql.Identifier(table_name)
                )
            )
            self.cursor.execute(
                sql.SQL("ALTER TABLE {migration_name} RENAME TO {real_name}").format(
                    real_name=sql.Identifier(table_name),
                    migration_name=sql.Identifier(
                        HelperGetNames.get_table_name(table_name, True)
                    ),
                )
            )

        # RECREATE triggers
        (
            pre_code,
            table_name_code,
            view_name_code,
            alter_table_code,  # should be sufficiently (re-)created with migrate command
            final_info_code,
            missing_handled_attributes,
            im_table_code,
            create_trigger_partitioned_sequences_code,
            create_trigger_1_1_relation_not_null_code,
            create_trigger_1_n_relation_not_null_code,
            create_trigger_n_m_relation_not_null_code,
            create_trigger_unique_ids_pair_code,
            create_trigger_notify_code,
            errors,
        ) = GenerateCodeBlocks.generate_the_code()
        sql_text = (
            view_name_code
            + alter_table_code
            + create_trigger_partitioned_sequences_code
            + create_trigger_1_1_relation_not_null_code
            + create_trigger_1_n_relation_not_null_code
            + create_trigger_n_m_relation_not_null_code
            + create_trigger_unique_ids_pair_code
            + create_trigger_notify_code
        )
        for collection_or_imt in im_tables | set(unified_replace_tables):
            to_drop_triggers = self.cursor.execute(
                sql.SQL("""SELECT
                        tgname AS trigger_name,
                        tgrelid::regclass AS table_name
                    FROM
                        pg_trigger
                    WHERE
                        tgrelid = {table_name}::regclass AND
                        tgname NOT LIKE 'RI_ConstraintTrigger_%';""").format(
                    table_name=HelperGetNames.get_table_name(collection_or_imt)
                )
            ).fetchall()
            for trigger_dict in to_drop_triggers:
                self.cursor.execute(
                    sql.SQL("DROP TRIGGER {trigger} ON {table};").format(
                        trigger=sql.SQL(trigger_dict["trigger_name"]),
                        table=sql.Identifier(trigger_dict["table_name"]),
                    )
                )
        self.cursor.execute(sql_text)

        self.update_sequences()

        MigrationHelper.write_line("finalization finished")
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
        if MigrationHelper.get_database_migration_index(self.cursor) < 100:
            for collection in replace_tables:
                self.cursor.execute(f"DROP TABLE {collection}_t;")
        if any(mi > 100 for mi in indices):
            for table_view in replace_tables.values():
                self.cursor.execute(f"DROP TABLE {table_view['table']};")
                self.cursor.execute(f"DROP VIEW {table_view['view']};")
