from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.alter_schema_helper import AlterSchemaHelper
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.patterns import (
    ArrayDiff,
    Column,
    ColumnDataSource,
    ColumnRef,
    InsertFromTables,
    Join,
    JoinOn,
    Renames,
    Table,
    TableDataSource,
    TableRef,
    UpdateFromTables,
    ValuesSource,
)
from openslides_backend.migrations.sql_helper import MigrationSqlHelper
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.filters import Filter, SqlArguments
from openslides_backend.shared.interfaces.logging import Logger
from openslides_backend.shared.patterns import Collection, Field


class BaseMigration:
    """Interface class for all migrations"""

    # -- Defined by developer --
    renames: Renames

    # Contains tables and fields that should be saved for retrieving data
    # in `data_manipulation`:
    #   * Collection or field gets removed but data for it is used
    #     to create/update other entries
    #   * Data from the field should be moved (with or without transformation)
    #     to the other table
    #   * Field type changes (usually it should lead to dropping
    #     old field and creating new)
    migration_tables: dict[Collection, list[Field]]

    # -- Internal --
    # Stores names of tables created from `migration_tables` and `switched_writing_side` for cleanup
    copied_tables: list[Table]

    # -- Defined in DiffMixin --
    # TODO: Implement here and in diff generator
    # Describes relations in which write field becomes a view field
    # due to rename (data should be moved).
    # Used in:
    #   * data_preparation: to save old writing side
    #   * data_manipulation: to perform move
    switched_writing_side: Any

    # Also include the new type of the field if it has to be transformed
    typed_migration_tables: dict[Collection, tuple[list[Field], dict[Field, str]]]

    # Contains:
    #   * String with statements that should be executed in the cleanup method.
    #     Currently needed for creating new views for the types changed for
    #     columns from enum_types_to_apply.
    # Used in:
    #   * cleanup: as the final step
    cleanup_statements: str

    def __init__(
        self, migration_cursor: Cursor[DictRow], logger: Logger, verbose: bool
    ) -> None:
        self.cursor = migration_cursor
        self.logger = logger
        self.verbose = verbose

    def check_prerequisites(self) -> str:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Checks all prerequisites for the migration.
        Returns:
            All errors collected. Empty string otherwise.
        """
        return ""

    def data_preparation(self) -> dict[str, Any] | None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Save data in helper tables or return it in a dict.
        """
        # TODO: after implementing switched_writing_side extend `migration_tables`
        # with collections and old writing side fields from `switched_writing_side``
        if getattr(self, "typed_migration_tables", None):
            self.log_debug_message("Creating migration tables.")
            copy_tables_queries = MigrationHelper.get_copy_tables_queries(
                self.typed_migration_tables
            )
            for query in copy_tables_queries.values():
                self.execute_query(query)
            self.copied_tables = list(copy_tables_queries.keys())
        return None

    def data_definition(self) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Applies all manual SQL DDL changes necessary.
            (Triggers and views are automatically recreated by the framework.)
        """

    def data_manipulation(self, stash: dict[str, Any] | None) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Writes all data changes necessary after the DDL changes.
        Input:
            stash: data that was previously stashed by data_preparation.
        """

    def cleanup(self) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Deletes leftovers of the migration.
        Input:
            cursor
        """
        for table in getattr(self, "copied_tables", []):
            self.execute_query(AlterSchemaHelper.get_drop_table_statement(table, True))
        if getattr(self, "cleanup_statements", None):
            self.execute_query(self.cleanup_statements)

    def execute_query(
        self,
        query: sql.Composed | sql.SQL | str,
        arguments: list[Any] | None = None,
        log: bool = True,
    ) -> None:
        if self.verbose and log:
            query_string = (
                query if isinstance(query, str) else query.as_string(self.cursor)
            )
            self.logger.debug(
                f"Executing migration query: {query_string}\n"
                f"With arguments: {arguments}"
            )
        self.cursor.execute(query, arguments)

    def log_debug_message(self, message: str) -> None:
        """
        Writes message with level debug to the log if migration is in verbose mode.
        """
        if self.verbose:
            self.logger.debug(message)

    # -- Helpers for data_manipulation --
    def _base_update_entries(
        self,
        target_table: TableRef,
        new_values: dict[Column, Any],
        filter_target_table: Filter | None = None,
        filter_migration_table: Filter | None = None,
        joined_tables: list[Join] | None = None,
    ) -> None:
        arguments: SqlArguments = []
        conditions = []

        set_part = MigrationSqlHelper.get_set_columns_part(new_values, arguments)
        if filter_target_table:
            conditions.append(
                self._build_filter_query(
                    filter_condition=filter_target_table,
                    arguments=arguments,
                    target_collection=target_table.collection,
                )
            )
        if filter_migration_table:
            assert not target_table.migration
            conditions.append(
                self._build_filter_query(
                    filter_condition=filter_migration_table,
                    arguments=arguments,
                    filter_other_table=Join(
                        right_table=TableRef(target_table.collection, True),
                        join_on=[
                            JoinOn(
                                right_column="id",
                                left_table=target_table,
                                left_column="id",
                            )
                        ],
                    ),
                )
            )
        if joined_tables:
            for join in joined_tables:
                assert join.filter_right_table is not None
                conditions.append(
                    self._build_filter_query(
                        filter_condition=join.filter_right_table,
                        arguments=arguments,
                        filter_other_table=join,
                        filter_condition_table_alias=join.right_table.table_name,
                    )
                )
        self.execute_query(
            MigrationSqlHelper.build_update_entries_sql(
                table_name=target_table.table_name,
                set_part=set_part,
                filter_condition=conditions or None,
            ),
            arguments,
        )

    def update_all_entries(
        self,
        target_table: TableRef,
        new_values: dict[Column, Any],
    ) -> None:
        """
        Sets the given simple values into the corresponding columns for all the collection entries.
        """
        self._base_update_entries(target_table=target_table, new_values=new_values)

    def update_matching_entries(
        self,
        target_table: TableRef,
        new_values: dict[Column, Any],
        filter_target_table: Filter | None = None,
        filter_migration_table: Filter | None = None,
        filter_with_joined_tables: list[Join] | None = None,
    ) -> None:
        """
        Builds and executes mass update statement for entries that match the lookup conditions.
        At least one filtering option must be provided:
            * filter_target_table - applies the filter to the target table (collection_t).
            * filter_migration_table - applies the filter to the related migration table (collection_m).
              Can be used only if target_table is a regular table (collection_t).
            * filter_with_joined_tables - applies filters to related tables through the specified
                joins. The target entry is updated if at least one matching row exists in the joined table.
        """
        if not any(
            [filter_target_table, filter_migration_table, filter_with_joined_tables]
        ):
            raise BadCodingException(
                "One out of 'filter_target_table', 'filter_migration_table' or 'joined_tables' must be defined."
            )
        if filter_migration_table and target_table.migration:
            raise BadCodingException(
                "'filter_target_table' must be used insted of 'filter_migration_table' when target_table is a migration table."
            )
        self._base_update_entries(
            target_table=target_table,
            new_values=new_values,
            filter_target_table=filter_target_table,
            filter_migration_table=filter_migration_table,
            joined_tables=filter_with_joined_tables,
        )

    def update_empty_cells(
        self,
        target_table: TableRef,
        column: Column,
        new_value: Any,
    ) -> None:
        """
        Sets the given simple value into the column for all the collection entries
        without the value in this column.
        """
        arguments: SqlArguments = []
        self.execute_query(
            MigrationSqlHelper.build_update_entries_sql(
                table_name=target_table.table_name,
                set_part=MigrationSqlHelper.get_set_columns_part(
                    {column: new_value}, arguments
                ),
                filter_condition=sql.SQL("{column} IS NULL").format(
                    column=sql.Identifier(column)
                ),
            ),
            arguments,
        )

    def update_from_values_map(
        self,
        target_table: TableRef,
        values_source: ValuesSource,
        filter_target_table: Filter | None = None,
        join_values_to_mig_table: bool = False,
    ) -> None:
        """
        Updates rows in the target table using values from `values_source`.

        Columns in `values_source.join_on_columns` are used to match source rows
        with target rows, while the remaining columns provide the values to set
        into the matching rows.

        Optional filter_condition can further restrict the rows being updated.

        `join_values_to_mig_table` allows to join the 'values_source' to the
        columns of the related migration table instead of the target table.
        """
        target_collection = target_table.collection
        arguments: SqlArguments = []
        filter_conditions: list[sql.Composable] = []
        join_conditions: list[sql.Composable]
        from_part: sql.Composable
        joined_tables_parts: (
            list[tuple[str | sql.Composed, list[sql.Composable]]] | None
        ) = None

        if join_values_to_mig_table:
            mig_table = TableRef(target_collection, True)
            from_part = sql.Identifier(mig_table.table_name)
            joined_tables_parts = [
                self._get_joined_values_data(values_source, mig_table, arguments)
            ]
            join_conditions = MigrationSqlHelper.get_conditions_for_join(
                self.cursor,
                mig_table.table_name,
                [JoinOn("id", target_table, "id")],
                values_source.match_nulls,
            )
        else:
            from_part = MigrationSqlHelper.build_values_table(values_source, arguments)
            join_conditions = self._get_join_conditions_for_values(
                values_source, target_table
            )
        filter_conditions = (
            [
                self._build_filter_query(
                    filter_target_table, arguments, target_collection
                )
            ]
            if filter_target_table is not None
            else []
        )
        self.execute_query(
            MigrationSqlHelper.build_update_entries_sql(
                table_name=target_table.table_name,
                set_part=sql.SQL(", ").join(
                    MigrationSqlHelper.get_column_assignment(
                        curs=self.cursor,
                        target_column=values_source.column_alias(column),
                        source_table=values_source.alias,
                        source_column=column,
                        type_source_table=target_table.table_name,
                    )
                    for column in values_source.data_source_columns
                ),
                source_table=from_part,
                joined_tables=joined_tables_parts,
                filter_condition=[*join_conditions, *filter_conditions],
            ),
            arguments,
        )

    def update_from_mig_table(
        self,
        collection: Collection,
        copy_from_source_table: list[ColumnDataSource],
        filter_target_table: Filter | None = None,
    ) -> None:
        self.update_from_other_table(
            UpdateFromTables(
                target_table=TableRef(collection, False),
                copy_data=[
                    TableDataSource(
                        source_table=Join(
                            TableRef(collection, True),
                            [JoinOn("id", TableRef(collection, False), "id")],
                        ),
                        value_definition=copy_from_source_table,
                    )
                ],
            ),
            filter_target_table,
        )

    def update_from_other_table(
        self,
        copy_from_source_tables: UpdateFromTables,
        filter_target_table: Filter | None = None,
    ) -> None:
        arguments: SqlArguments = []
        joined_tables_parts: list[tuple[str | sql.Composed, list[sql.Composable]]] = (
            self._get_joined_tables_data(
                copy_from_source_tables.joined_sources, arguments
            )
        )

        source_table = joined_tables_parts[0][0]
        filters: list[sql.Composable] = joined_tables_parts[0][1]
        joined_tables = joined_tables_parts[1:]

        if filter_target_table:
            filters.append(
                self._build_filter_query(
                    filter_target_table,
                    arguments,
                    copy_from_source_tables.target_table.collection,
                    filter_condition_table_alias=copy_from_source_tables.target_table.table_name,
                )
            )

        assert isinstance(source_table, str)
        self.execute_query(
            MigrationSqlHelper.build_update_entries_sql(
                table_name=copy_from_source_tables.target_table.table_name,
                set_part=sql.SQL(", ").join(
                    MigrationSqlHelper.get_value_assignment(target_column, value)
                    for target_column, value in zip(
                        copy_from_source_tables.target_columns,
                        self._normalize_select_columns(
                            copy_from_source_tables.select_columns,
                            copy_from_source_tables.target_table,
                            copy_from_source_tables.target_columns,
                        ),
                    )
                ),
                source_table=sql.Identifier(source_table),
                joined_tables=joined_tables,
                filter_condition=filters,
            ),
            arguments,
        )

    def insert_from_other_table(
        self,
        target_collection: Collection,
        copy_from_source_tables: InsertFromTables,
        values_source: ValuesSource | None = None,
        return_fields: list[str] | None = [],
    ) -> list[dict[str, Any]]:
        """
        Inserts rows into table defined by 'target_collection' using values
        selected from the joined tables defined by 'copy_from_source_tables'.
        Optional filters for the source tables can restrict which rows are used
        as the source.

        Optional 'values_source' can be used to provide additional target values.

        Target columns must not be defined more than once across 'values_source'
        and 'copy_from_source_tables'.
        """
        arguments: SqlArguments = []
        target_table = TableRef(target_collection, False)

        target_columns = copy_from_source_tables.target_columns.copy()
        select_columns = copy_from_source_tables.select_columns.copy()
        joined_tables_parts = self._get_joined_tables_data(
            copy_from_source_tables.joined_sources, arguments
        )

        if values_source is not None:
            if duplicates := set(values_source.target_columns) & set(target_columns):
                raise BadCodingException(
                    f"'copy_from_source_tables' and 'values_source' define multiple sources for column(s): {duplicates}."
                )
            joined_tables_parts.append(
                self._get_joined_values_data(
                    values_source,
                    copy_from_source_tables.root_source_table,
                    arguments,
                )
            )
            target_columns.extend(values_source.target_columns)
            select_columns.extend(values_source.select_columns)

        filter_condition = (
            self._build_filter_query(
                copy_from_source_tables.root_source.filter_right_table,
                arguments,
                copy_from_source_tables.root_source_table.collection,
                filter_condition_table_alias=copy_from_source_tables.root_source_table.table_name,
            )
            if copy_from_source_tables.root_source.filter_right_table
            else None
        )
        is_intermediate_table = any(
            target_collection.startswith(prefix) for prefix in ["gm_", "nm_"]
        )
        if (
            isinstance(return_fields, list)
            and not is_intermediate_table
            and "id" not in return_fields
        ):
            return_fields.append("id")
        self.execute_query(
            MigrationSqlHelper.build_insert_from_other_table_sql(
                target_table=target_table.table_name,
                target_columns=MigrationSqlHelper.join_columns(target_columns),
                select_columns=self._join_select_columns(
                    select_columns, target_table, target_columns
                ),
                source_table=copy_from_source_tables.root_source_table.table_name,
                joined_tables=joined_tables_parts,
                condition=filter_condition,
                return_fields=return_fields,
            ),
            arguments,
        )
        return self.cursor.fetchall()

    def update_array(
        self,
        target_table: TableRef,
        column: Column,
        diff: ArrayDiff,
        filter_target_table: Filter | None = None,
    ) -> None:
        """
        Updates an array column using add/remove/replace operations.
        The resulting array contains unique values sorted in ascending order.
        """
        filter_arguments: SqlArguments = []
        values_arguments: list[SqlArguments] = []
        array_type = MigrationSqlHelper.get_array_type(
            target_table.collection, column, self.cursor
        )

        query = MigrationSqlHelper.build_update_entries_sql(
            table_name=target_table.table_name,
            set_part=MigrationSqlHelper.build_array_update_part(
                column=column,
                array_type=array_type,
                source=MigrationSqlHelper.build_array_source_expression(
                    column, diff.replace, values_arguments, array_type
                ),
                remove=MigrationSqlHelper.build_array_remove_expression(
                    diff.remove, values_arguments, array_type
                ),
                add=MigrationSqlHelper.build_array_add_expression(
                    diff.add, values_arguments, array_type
                ),
            ),
            filter_condition=(
                self._build_filter_query(
                    filter_target_table, filter_arguments, target_table.collection
                )
                if filter_target_table is not None
                else None
            ),
        )
        self.execute_query(query, [*values_arguments, *filter_arguments])

    # -- Helpers for intermediate data generation --
    def _build_filter_query(
        self,
        filter_condition: Filter,
        arguments: SqlArguments,
        target_collection: Collection | None = None,
        filter_other_table: Join | None = None,
        filter_condition_table_alias: str | None = None,
    ) -> sql.Composable:
        """
        Builds lookup part of the SQL query. Also updates arguments.
        Can filter array field only if it belongs to the regular table (ending with _t).
        """
        filtered_tables = [target_collection, filter_other_table]
        if all(filtered_tables):
            raise BadCodingException(
                "Only one out of 'target_collection' or 'filter_other_table' can be defined."
            )
        if not any(filtered_tables):
            raise BadCodingException(
                "Table that should be filtered has to be defined with 'target_collection' or 'filter_other_table'."
            )

        if filter_other_table is None:
            assert target_collection is not None
            return MigrationSqlHelper.build_filter_str(
                filter_condition,
                arguments,
                target_collection,
                filter_condition_table_alias or "",
            )
        else:
            return MigrationSqlHelper.get_lookup_part_from_other_table(
                self.cursor,
                filter_other_table,
                MigrationSqlHelper.build_filter_str(
                    filter_condition,
                    arguments,
                    filter_other_table.right_table.collection,
                    filter_condition_table_alias or "",
                ),
            )

    def _get_join_conditions_for_values(
        self, values_source: ValuesSource, left_table: TableRef
    ) -> list[sql.Composable]:
        return MigrationSqlHelper.get_conditions_for_join(
            self.cursor,
            values_source.alias,
            [
                JoinOn(column, left_table, values_source.column_alias(column))
                for column in values_source.join_on_columns
            ],
            values_source.match_nulls,
        )

    def _get_joined_tables_data(
        self,
        join_tables: list[TableDataSource],
        arguments: SqlArguments,
    ) -> list[tuple[str | sql.Composed, list[sql.Composable]]]:
        result: list[tuple[str | sql.Composed, list[sql.Composable]]] = []
        for data_source in join_tables:
            source_table = data_source.source_table
            conditions: list[sql.Composable] = (
                MigrationSqlHelper.get_conditions_for_join(
                    self.cursor,
                    source_table.right_table.table_name,
                    source_table.join_on,
                )
            )
            if source_table.filter_right_table is not None:
                conditions.append(
                    self._build_filter_query(
                        source_table.filter_right_table,
                        arguments,
                        source_table.right_table.collection,
                        filter_condition_table_alias=source_table.right_table.table_name,
                    )
                )
            result.append((source_table.right_table.table_name, conditions))
        return result

    def _get_joined_values_data(
        self,
        values_source: ValuesSource,
        left_table: TableRef,
        arguments: SqlArguments,
    ) -> tuple[sql.Composed, list[sql.Composable]]:
        return (
            MigrationSqlHelper.build_values_table(values_source, arguments),
            self._get_join_conditions_for_values(values_source, left_table),
        )

    def _join_select_columns(
        self,
        select_columns: list[ColumnRef | sql.Composable],
        target_table: TableRef,
        target_columns: list[Column],
    ) -> sql.Composed:
        return sql.SQL(", ").join(
            self._normalize_select_columns(select_columns, target_table, target_columns)
        )

    def _normalize_select_columns(
        self,
        select_columns: list[ColumnRef | sql.Composable],
        target_table: TableRef,
        target_columns: list[Column],
    ) -> list[sql.Composable]:
        MigrationSqlHelper.add_type_to_column_refs(
            self.cursor,
            target_table.table_name,
            [
                (select_column, target_column)
                for select_column, target_column in zip(select_columns, target_columns)
                if isinstance(select_column, ColumnRef)
            ],
        )
        return [
            column.identifier if isinstance(column, ColumnRef) else column
            for column in select_columns
        ]
