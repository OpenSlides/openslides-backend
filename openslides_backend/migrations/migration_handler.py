import re
import string
from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb

from meta.dev.src.generate_sql_schema import GenerateCodeBlocks, HelperGetNames
from openslides_backend.models.base import model_registry
from openslides_backend.shared.exceptions import CommandNotImplemented

from ..migrations.exceptions import (
    InvalidMigrationCommand,
    MigrationException,
    MigrationSetupException,
)
from ..migrations.migration_helper import OLD_TABLES, MigrationHelper, MigrationState
from ..shared.handlers.base_handler import BaseHandler
from ..shared.interfaces.env import Env
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services


class MigrationHandler(BaseHandler):
    # Including pk_ as a precaution here since it's actually a case and if it ever was applied on table code.
    # Would maybe have to add other constraint prefixes if their naming pattern changed.
    TABLE_RE = re.compile(r"\b(?!pk_|tr_|equal_)([A-Za-z0-9_.]+)(_t)\b")
    TRIGGER_BLOCK_RE = re.compile(
        r"(CREATE\s+(?:CONSTRAINT\s+)?TRIGGER\b.*?;)", re.IGNORECASE | re.DOTALL
    )

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
        table_m = sql.Identifier(
            HelperGetNames.get_table_name(table_name, migration=True)
        )
        table_t = sql.Identifier(table_name)
        self.cursor.execute(
            sql.SQL("CREATE TABLE {table_m} (LIKE {table_t} INCLUDING ALL);").format(
                table_m=table_m, table_t=table_t
            )
        )

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
        im_tables_without_suffix = {table[:-2] for table in im_tables}

        # COPY intermediate tables
        for table_name in im_tables:
            self.copy_table(table_name)

        # COPY fkey constraints
        for table_name in im_tables | {
            r_tables["table"]
            for r_tables in unified_replace_tables.values()
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
                foreign_collection = result["foreign_table_name"][:-2]
                # TODO: find out how to do this.
                # if not unified_replace_tables[foreign_collection].get("to_delete"):
                if foreign_collection in unified_replace_tables:
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
            if base in unified_replace_tables or base in im_tables_without_suffix:
                return base + "_m"
            else:
                return base + "_t"

        all_tables_to_be_replaced = {
            HelperGetNames.get_table_name(collection)
            for collection in unified_replace_tables
        }
        all_tables_to_be_replaced |= im_tables
        all_tables_to_be_replaced_without_suffix = (
            set(unified_replace_tables) | im_tables_without_suffix
        )
        # COPY views for migration reads
        max_index = MigrationHelper.get_backend_migration_index()
        max_index_replace_tables = MigrationHelper.get_replace_tables_from_database(
            self.cursor, max_index
        )
        for view in MigrationHelper.get_all_view_definitions(self.cursor):
            view_def = view["viewdef"]
            collection = view["relname"]
            mig_view_name = unified_replace_tables.get(
                collection, {"view": collection + "vm"}
            )["view"]
            if any(table in view_def for table in all_tables_to_be_replaced):
                view_def = self.TABLE_RE.sub(replace_suffix, view_def)
                self.cursor.execute(
                    sql.SQL("CREATE VIEW {view_m} AS {viewdef};").format(
                        view_m=sql.Identifier(mig_view_name),
                        viewdef=sql.SQL(view_def),
                    )
                )
                # If created view is not created because of replace tables:
                if collection not in all_tables_to_be_replaced_without_suffix:
                    # additional_views.append(collection)
                    # TODO I'm unsatisfied with writing this information to that key of replace tables.
                    max_index_replace_tables[collection] = {
                        "additional_view": collection
                    }
        # Not using set_migration_info because we don't want to commit the connection.
        self.cursor.execute(
            sql.SQL("""
                UPDATE version SET replace_tables={max_index_replace_tables}
                WHERE migration_index = {max_index};
                """).format(
                max_index_replace_tables=Jsonb(max_index_replace_tables),
                max_index=max_index,
            )
        )

        # RECREATE some relevant triggers
        # May be error prone due to changing constraints
        (
            enum_definitions,
            pre_code,
            table_name_code,
            view_name_code,
            alter_table_code,
            final_info_code,
            missing_handled_attributes,
            missing_handled_collections_meta_attributes,
            im_table_code,
            # TODO partitioned sequences trigger need to be migrated alongside others once a migration starts to write new data rows triggering these.
            # Otherwise the new sequential numbers wouldn't be generated
            # _m sequences could simply be deleted during finalization or - depending on reliability - be renamed.
            create_trigger_partitioned_sequences_code,
            create_trigger_1_1_relation_not_null_code,
            create_trigger_1_n_relation_not_null_code,
            create_trigger_n_m_relation_not_null_code,
            create_trigger_prevent_updates_code,
            create_trigger_unique_ids_pair_code,
            create_trigger_equal_fields_code,
            create_trigger_notify_code,
            errors,
        ) = GenerateCodeBlocks.generate_the_code()
        sql_text = (
            create_trigger_1_1_relation_not_null_code
            + create_trigger_1_n_relation_not_null_code
            + create_trigger_n_m_relation_not_null_code
            + create_trigger_unique_ids_pair_code
            + create_trigger_equal_fields_code
        )
        # replace with the migration names before execute
        modified_blocks = []
        view_re = re.compile(r"\B'([A-Za-z0-9_.]+)'\B")

        def add_suffix(m: re.Match) -> str:
            base = m.group(1)
            if base in unified_replace_tables:
                return f"'{base}vm'"
            else:
                return f"'{base}'"

        for match in self.TRIGGER_BLOCK_RE.finditer(sql_text):
            block = match.group(0)
            if table_match := self.TABLE_RE.search(block):
                col_or_im = table_match.group(1)[:-2]
                if (
                    col_or_im in unified_replace_tables
                    or col_or_im in im_tables_without_suffix
                ):
                    modified_block = self.TABLE_RE.sub(replace_suffix, block)
                    modified_blocks.append(view_re.sub(add_suffix, modified_block))
        sql_text = "".join(modified_blocks)
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
        for index, module_name in MigrationHelper.migrations.items():
            mig_class = MigrationHelper.get_migration_class(module_name)

            self.logger.info("Executing migration: " + module_name)

            # checks wether the methods are available and executes them.
            mig_class.data_definition(self.cursor)
            mig_class.data_manipulation(self.cursor)

            MigrationHelper.set_database_migration_info(
                self.cursor, index, MigrationState.FINALIZATION_REQUIRED
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
                for module_name in MigrationHelper.migrations.values():
                    mig_class = MigrationHelper.get_migration_class(module_name)
                    self.logger.info("Pre check: " + module_name + " ...")
                    if errors := mig_class.check_prerequisites(self.cursor):
                        if minimum_required_index:
                            MigrationHelper.set_database_migration_info(
                                self.cursor,
                                minimum_required_index["min"],
                                MigrationState.MIGRATION_REQUIRED,
                            )
                        errors = (
                            f"Pre check for migration {module_name} failed.\n{errors}"
                        )
                        self.logger.info(errors)
                        raise MigrationSetupException(errors)
                MigrationHelper.write_line("migration started")
                self.logger.info("Preparing migrations ...")
                self.set_public_tables_read_only()
                self.setup_migration_relations()
                self.execute_migrations()
                MigrationHelper.write_line("migration finished")
                MigrationHelper.migrate_thread_stream_can_be_closed = True
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
            # TODO: This code does nothing. Delete it or fix it by putting a not in front of the if clause or smth.
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
    def close_migrate_thread_stream(cls) -> None:
        """
        Closes the migration threads io stream.
        """
        assert MigrationHelper.migrate_thread_stream

        MigrationHelper.migrate_thread_stream.close()
        MigrationHelper.migrate_thread_stream = None
        MigrationHelper.migrate_thread_stream_can_be_closed = False
        MigrationHelper.migrate_thread_exception = None

    def finalize(self) -> None:
        """
        Executes the cleanup method and copies tables into place.
        Also sets the migration info accordingly.
        """
        state = MigrationHelper.get_migration_state(self.cursor)
        match state:
            case MigrationState.FINALIZED:
                return
            case MigrationState.FINALIZATION_REQUIRED:
                self.logger.info("Finalize migrations.")
            case _:
                raise MigrationException(
                    f"State is: {state} Finalization not possible if it's not required."
                )

        MigrationHelper.write_line("finalization started")
        unified_replace_tables, relevant_mis = (
            MigrationHelper.get_unified_replace_tables_from_database(self.cursor)
        )
        for mi in relevant_mis:
            MigrationHelper.set_database_migration_info(
                self.cursor, mi, MigrationState.FINALIZATION_RUNNING
            )

        self.logger.info("Executing cleanup functions ...")
        for index, module_name in MigrationHelper.migrations.items():
            MigrationHelper.get_migration_class(module_name).cleanup(self.cursor)

        self.logger.info("Integrating data into origin tables ...")
        # First delete all additional views to prevent deleting a table that is depended upon
        for r_tables in unified_replace_tables.values():
            if additional_view := r_tables.get("additional_view"):
                self.cursor.execute(
                    sql.SQL("DROP VIEW {migration_name};").format(
                        migration_name=sql.Identifier(additional_view),
                    )
                )

        im_tables = set()
        # Do the general replacement
        for collection, migration_names in unified_replace_tables.items():
            if "table" not in migration_names:
                continue
            # Will also drop attached intermediate tables and views.
            self.cursor.execute(
                sql.SQL("DROP TABLE {real_name} CASCADE;").format(
                    real_name=sql.Identifier(collection + "_t")
                )
            )
            self.cursor.execute(
                sql.SQL(
                    "ALTER TABLE IF EXISTS {migration_name} RENAME TO {real_name}"
                ).format(
                    real_name=sql.Identifier(collection + "_t"),
                    migration_name=sql.Identifier(migration_names["table"]),
                )
            )
            self.cursor.execute(
                sql.SQL(
                    "ALTER SEQUENCE IF EXISTS {collection}_m_id_seq RENAME TO {collection}_t_id_seq;"
                ).format(collection=sql.SQL(collection))
            )
            # Will be recreated for origin table below.
            # TODO I dont want IF EXISTS probably need use of real_replace_tables
            self.cursor.execute(
                sql.SQL("DROP VIEW IF EXISTS {migration_name};").format(
                    migration_name=sql.Identifier(migration_names["view"]),
                )
            )
            im_tables.update(migration_names["im_tables"])

        # RENAME intermediate tables
        # TODO move this entire block before handling of main tables
        for table_name in im_tables:
            self.cursor.execute(
                sql.SQL("DROP TABLE {real_name};").format(
                    real_name=sql.Identifier(table_name)
                )
            )
            self.cursor.execute(
                sql.SQL(
                    "ALTER TABLE IF EXISTS {migration_name} RENAME TO {real_name}"
                ).format(
                    real_name=sql.Identifier(table_name),
                    migration_name=sql.Identifier(
                        HelperGetNames.get_table_name(table_name, migration=True)
                    ),
                )
            )

        self.logger.info("Reapplying schema parts ...")
        # RECREATE triggers
        (
            enum_definitions,
            pre_code,
            table_name_code,
            view_name_code,
            alter_table_code,  # should be sufficiently (re-)created with migrate command
            final_info_code,
            missing_handled_attributes,
            missing_handled_collections_meta_attributes,
            im_table_code,
            create_trigger_partitioned_sequences_code,
            create_trigger_1_1_relation_not_null_code,
            create_trigger_1_n_relation_not_null_code,
            create_trigger_n_m_relation_not_null_code,
            create_trigger_prevent_updates_code,
            create_trigger_unique_ids_pair_code,
            create_trigger_equal_fields_code,
            create_trigger_notify_code,
            errors,
        ) = GenerateCodeBlocks.generate_the_code()
        # TODO I don't like this CREATE OR REPLACE
        # TODO doesn't this need to happen early on? Like before renaming? No, but the idx isn't needed for those pointing to a mig table.
        # Maybe there is a way to reimplement generate_the_code behaviour to get only deleted views.
        # Or use detection similar to trigger blocks
        # TODO this fails for 101 bc the table assignment_category_t doesn't exist.
        # Why hasn't it been created before?
        self.cursor.execute((view_name_code).replace("CREATE", "CREATE OR REPLACE"))

        # Recreate fkeys and indices
        im_tables_without_suffix = {table[:-2] for table in im_tables}
        relevant_blocks = []
        fkey_re = re.compile(r"(ALTER TABLE\s\b.*?;)", re.IGNORECASE | re.DOTALL)
        fkey_index_re = re.compile(
            r"(ALTER TABLE\s\b.*?\);)", re.IGNORECASE | re.DOTALL
        )
        real_replace_tables = {
            collection
            for collection, r_tables in unified_replace_tables.items()
            if (r_tables.get("table"))
        }
        for match in fkey_index_re.finditer(alter_table_code):
            block = match.group(0)
            if table_match := self.TABLE_RE.search(block):
                col_or_im = table_match.group(1)
                if (
                    col_or_im in real_replace_tables
                    or col_or_im in im_tables_without_suffix
                ):
                    relevant_blocks.append(block)
                elif (
                    col_or_im in unified_replace_tables
                    and (table_match := self.TABLE_RE.search(block, table_match.end()))
                    and table_match.group(1) in real_replace_tables
                    and (fkey_match := fkey_re.search(block))
                ):
                    # `col_or_im` is an origin table that does not get replaced (not in
                    # real_replace_tables) but loses its foreign keys to `table_match`
                    relevant_blocks.append(fkey_match.group(1))
        sql_text = "".join(relevant_blocks)
        self.cursor.execute(sql_text)

        sql_text = (
            create_trigger_partitioned_sequences_code
            + create_trigger_1_1_relation_not_null_code
            + create_trigger_1_n_relation_not_null_code
            + create_trigger_n_m_relation_not_null_code
            + create_trigger_prevent_updates_code
            + create_trigger_unique_ids_pair_code
            + create_trigger_notify_code
            + create_trigger_equal_fields_code
        )
        relevant_blocks = []
        # Find all blocks in the shape of CREATE [CONSTRAINT] TRIGGER [..]
        for match in self.TRIGGER_BLOCK_RE.finditer(sql_text):
            block = match.group(0)
            if table_match := self.TABLE_RE.search(block):
                col_or_im = table_match.group(1)
                if (
                    # TODO doesn't this also need to be real_replace_tables?
                    col_or_im in unified_replace_tables
                    or col_or_im in im_tables_without_suffix
                ):
                    relevant_blocks.append(block)
        sql_text = "".join(relevant_blocks)
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
        raise CommandNotImplemented("The reset route is not implemented yet.")
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
        for collection in replace_tables:
            self.cursor.execute(f"DROP TABLE {collection}_m;")
        if any(mi > 100 for mi in indices):
            for table_view in replace_tables.values():
                self.cursor.execute(f"DROP TABLE {table_view['table']};")
                self.cursor.execute(f"DROP VIEW {table_view['view']};")
