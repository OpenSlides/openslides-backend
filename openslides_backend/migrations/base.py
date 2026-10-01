from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.alter_schema_helper import AlterSchemaHelper
from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.patterns import (
    ArrayDiff,
    Column,
    ColumnDataSource,
    ExtendedSqlArguments,
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

    @staticmethod
    def check_prerequisites(curs: Cursor[DictRow]) -> str:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Checks all prerequisites for the migration.
        Input:
            cursor
        Returns:
            All errors collected. Empty string otherwise.
        """
        return ""

    def data_preparation(self, curs: Cursor[DictRow]) -> dict[str, Any] | None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Save data in helper tables or return it in a dict.
        Input:
            cursor
        """
        # TODO: after implementing switched_writing_side extend `migration_tables`
        # with collections and old writing side fields from `switched_writing_side``
        if getattr(self, "typed_migration_tables", None):
            self.copied_tables = MigrationHelper.copy_tables(
                curs, self.typed_migration_tables
            )
        return None

    @staticmethod
    def data_definition(curs: Cursor[DictRow]) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Applies all manual SQL DDL changes necessary.
            (Triggers and views are automatically recreated by the framework.)
        Input:
            cursor
        """

    def data_manipulation(
        self, curs: Cursor[DictRow], stash: dict[str, Any] | None
    ) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Writes all data changes necessary after the DDL changes.
        Input:
            cursor
            stash: data that was previously stashed by data_preparation.
        """

    def cleanup(self, curs: Cursor[DictRow]) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Deletes leftovers of the migration.
        Input:
            cursor
        """
        for table in getattr(self, "copied_tables", []):
            curs.execute(AlterSchemaHelper.get_drop_table_statement(table, True))
        if getattr(self, "cleanup_statements", None):
            curs.execute(self.cleanup_statements)

    # -- Helpers for data_manipulation --
    @staticmethod
    def _base_update_entries(
        curs: Cursor[DictRow],
        collection: Collection,
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
                BaseMigration._build_filter_query(
                    filter_condition=filter_target_table,
                    arguments=arguments,
                    target_collection=collection,
                )
            )
        if filter_migration_table:
            conditions.append(
                BaseMigration._build_filter_query(
                    filter_condition=filter_migration_table,
                    arguments=arguments,
                    filter_other_table=Join(
                        right_table=TableRef(collection, True),
                        join_on=[
                            JoinOn(
                                right_column="id",
                                left_table=TableRef(collection, False),
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
                    BaseMigration._build_filter_query(
                        filter_condition=join.filter_right_table,
                        arguments=arguments,
                        filter_other_table=join,
                    )
                )
        curs.execute(
            MigrationSqlHelper.build_update_entries_sql(
                collection_or_table_name=collection,
                set_part=set_part,
                filter_condition=conditions or None,
            ),
            arguments,
        )

    @staticmethod
    def update_all_entries(
        curs: Cursor[DictRow],
        collection: Collection,
        new_values: dict[Column, Any],
    ) -> None:
        """
        Sets the given simple values into the corresponding columns for all the collection entries.
        """
        BaseMigration._base_update_entries(
            curs,
            collection=collection,
            new_values=new_values,
        )

    @staticmethod
    def update_matching_entries(
        curs: Cursor[DictRow],
        collection: Collection,
        new_values: dict[Column, Any],
        filter_target_table: Filter | None = None,
        filter_migration_table: Filter | None = None,
        filter_with_joined_tables: list[Join] | None = None,
    ) -> None:
        """
        Builds and executes mass update statement for entries that match the lookup conditions.
        At least one filtering option must be provided:
            * filter_target_table - applies the filter to the target table (collection_t).
            * filter_migration_table - applies the filter to the migration table (collection_m).
            * filter_with_joined_tables - applies filters to related tables through the specified
                joins. The target entry is updated if at least one matching row exists in the joined table.
        """
        if not any(
            [filter_target_table, filter_migration_table, filter_with_joined_tables]
        ):
            raise BadCodingException(
                "One out of 'filter_target_table', 'filter_migration_table' or 'joined_tables' must be defined."
            )
        BaseMigration._base_update_entries(
            curs,
            collection=collection,
            new_values=new_values,
            filter_target_table=filter_target_table,
            filter_migration_table=filter_migration_table,
            joined_tables=filter_with_joined_tables,
        )

    @staticmethod
    def update_empty_cells(
        curs: Cursor[DictRow],
        collection: Collection,
        column: Column,
        new_value: Any,
    ) -> None:
        """
        Sets the given simple value into the column for all the collection entries
        without the value in this column.
        """
        arguments: SqlArguments = []
        curs.execute(
            MigrationSqlHelper.build_update_entries_sql(
                collection_or_table_name=collection,
                set_part=MigrationSqlHelper.get_set_columns_part(
                    {column: new_value}, arguments
                ),
                filter_condition=sql.SQL("{column} IS NULL").format(
                    column=sql.Identifier(column)
                ),
            ),
            arguments,
        )

    @staticmethod
    def update_from_values_map(
        curs: Cursor[DictRow],
        target_collection: Collection,
        values_source: ValuesSource,
        filter_condition: Filter | None = None,
    ) -> None:
        """
        Updates rows in the target collection using values from `values_source`.

        Columns in `values_source.join_on_columns` are used to match source rows
        with target rows, while the remaining columns provide the values to set
        into the matching rows.

        Optional filter_condition can further restrict the rows being updated.
        """
        arguments: SqlArguments = []

        from_part = MigrationSqlHelper.build_values_table(values_source, arguments)
        join_conditions = BaseMigration._get_join_conditions_for_values(
            values_source, TableRef(target_collection, False)
        )
        filter_conditions = (
            [
                BaseMigration._build_filter_query(
                    filter_condition, arguments, target_collection
                )
            ]
            if filter_condition is not None
            else []
        )
        curs.execute(
            MigrationSqlHelper.build_update_entries_sql(
                collection_or_table_name=target_collection,
                set_part=sql.SQL(", ").join(
                    MigrationSqlHelper.get_column_assignment(
                        target_column=column,
                        source_table=values_source.alias,
                    )
                    for column in values_source.target_columns
                ),
                source_table=from_part,
                filter_condition=[*join_conditions, *filter_conditions],
            ),
            arguments,
        )

    @staticmethod
    def update_from_mig_table(
        curs: Cursor[DictRow],
        collection: Collection,
        copy_from_source_table: list[ColumnDataSource],
        filter_target_table: Filter | None = None,
    ) -> None:
        BaseMigration.update_from_other_table(
            curs,
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

    @staticmethod
    def update_from_other_table(
        curs: Cursor[DictRow],
        copy_from_source_tables: UpdateFromTables,
        filter_target_table: Filter | None = None,
    ) -> None:
        arguments: SqlArguments = []
        joined_tables_parts: list[tuple[str | sql.Composed, list[sql.Composable]]] = (
            BaseMigration._get_joined_tables_data(
                copy_from_source_tables.joined_sources, arguments
            )
        )

        source_table = joined_tables_parts[0][0]
        filters: list[sql.Composable] = joined_tables_parts[0][1]
        joined_tables = joined_tables_parts[1:]

        if filter_target_table:
            filters.append(
                BaseMigration._build_filter_query(
                    filter_target_table,
                    arguments,
                    copy_from_source_tables.target_table.collection,
                    filter_condition_table_alias=copy_from_source_tables.target_table.table_name,
                )
            )

        assert isinstance(source_table, str)
        curs.execute(
            MigrationSqlHelper.build_update_entries_sql(
                collection_or_table_name=copy_from_source_tables.target_table.table_name,
                set_part=sql.SQL(", ").join(
                    MigrationSqlHelper.get_value_assignment(target_column, value)
                    for target_column, value in copy_from_source_tables.copy_data_map.items()
                ),
                source_table=sql.Identifier(source_table),
                joined_tables=joined_tables,
                filter_condition=filters,
            ),
            arguments,
        )

    @staticmethod
    def insert_from_other_table(
        curs: Cursor[DictRow],
        target_collection: Collection,
        copy_from_source_tables: InsertFromTables,
        values_source: ValuesSource | None = None,
        return_fields: list[str] = [],
    ) -> dict[int, dict[str, Any]]:
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

        target_columns = copy_from_source_tables.target_columns.copy()
        select_columns = copy_from_source_tables.select_columns.copy()
        joined_tables_parts = BaseMigration._get_joined_tables_data(
            copy_from_source_tables.joined_sources, arguments
        )

        if values_source is not None:
            if duplicates := set(values_source.target_columns) & set(target_columns):
                raise BadCodingException(
                    f"'copy_from_source_tables' and 'values_source' define multiple sources for column(s): {duplicates}."
                )
            joined_tables_parts.append(
                BaseMigration._get_joined_values_data(
                    values_source,
                    copy_from_source_tables.root_source,
                    arguments,
                )
            )
            target_columns.extend(values_source.target_columns)
            select_columns.extend(values_source.select_columns)

        filter_condition = (
            BaseMigration._build_filter_query(
                copy_from_source_tables.filter_main_source_table,
                arguments,
                target_collection,
                filter_condition_table_alias=copy_from_source_tables.root_source.table_name,
            )
            if copy_from_source_tables.filter_main_source_table
            else None
        )

        curs.execute(
            MigrationSqlHelper.build_insert_from_other_table_sql(
                target_table=HelperGetNames.get_table_name(target_collection),
                target_columns=MigrationSqlHelper.join_columns(target_columns),
                select_columns=sql.SQL(", ").join(select_columns),
                source_table=copy_from_source_tables.root_source.table_name,
                joined_tables=joined_tables_parts,
                condition=filter_condition,
                return_fields=["id", *return_fields],
            ),
            arguments,
        )
        return {item["id"]: item for item in curs.fetchall()}

    @staticmethod
    def update_array(
        curs: Cursor[DictRow],
        collection: str,
        column: Column,
        diff: ArrayDiff,
        filter_target_table: Filter | None = None,
    ) -> None:
        """
        Updates an array column using add/remove/replace operations.
        The resulting array contains unique values sorted in ascending order.
        """
        filter_arguments: SqlArguments = []
        values_arguments: ExtendedSqlArguments = []
        array_type = MigrationSqlHelper.get_array_type(collection, column, curs)

        query = MigrationSqlHelper.build_update_entries_sql(
            collection_or_table_name=collection,
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
                BaseMigration._build_filter_query(
                    filter_target_table, filter_arguments, collection
                )
                if filter_target_table is not None
                else None
            ),
        )
        curs.execute(query, [*values_arguments, *filter_arguments])

    # -- Helpers for intermediate data generation --
    @staticmethod
    def _build_filter_query(
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
                filter_other_table,
                MigrationSqlHelper.build_filter_str(
                    filter_condition,
                    arguments,
                    filter_other_table.right_table.collection,
                    filter_condition_table_alias or "",
                ),
            )

    @staticmethod
    def _get_join_conditions_for_values(
        values_source: ValuesSource, left_table: TableRef
    ) -> list[sql.Composable]:
        return MigrationSqlHelper.get_conditions_for_join(
            values_source.alias,
            [
                JoinOn(column, left_table, column)
                for column in values_source.join_on_columns
            ],
        )

    @staticmethod
    def _get_joined_tables_data(
        join_tables: list[TableDataSource], arguments: SqlArguments
    ) -> list[tuple[str | sql.Composed, list[sql.Composable]]]:
        result: list[tuple[str | sql.Composed, list[sql.Composable]]] = []
        for data_source in join_tables:
            source_table = data_source.source_table
            conditions: list[sql.Composable] = (
                MigrationSqlHelper.get_conditions_for_join(
                    source_table.right_table.table_name, source_table.join_on
                )
            )
            if source_table.filter_right_table is not None:
                conditions.append(
                    BaseMigration._build_filter_query(
                        source_table.filter_right_table,
                        arguments,
                        source_table.right_table.collection,
                        filter_condition_table_alias=source_table.right_table.table_name,
                    )
                )
            result.append((source_table.right_table.table_name, conditions))
        return result

    @staticmethod
    def _get_joined_values_data(
        values_source: ValuesSource,
        left_table: TableRef,
        arguments: SqlArguments,
    ) -> tuple[sql.Composed, list[sql.Composable]]:
        return (
            MigrationSqlHelper.build_values_table(values_source, arguments),
            BaseMigration._get_join_conditions_for_values(values_source, left_table),
        )
