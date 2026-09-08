from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.alter_schema_helper import AlterSchemaHelper
from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.patterns import Renames, Table
from openslides_backend.shared.filters import BaseSqlQueryHelper, Filter, SqlArguments
from openslides_backend.shared.patterns import Collection, Field


class BaseMigrationSqlHelper(BaseSqlQueryHelper):
    # -- Override not implemented parent method --
    @staticmethod
    def get_enum_array_name(
        collection: str, column: str, curs: Cursor[DictRow]
    ) -> str | None:
        return (
            curs.execute(
                sql.SQL(
                    "SELECT t.typelem FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid WHERE attrelid = {table_name}::regclass AND attname = {column_name};"
                ).format(
                    table_name=sql.Identifier(
                        HelperGetNames.get_table_name(collection)
                    ),
                    column_name=sql.Identifier(column),
                )
            ).fetchone()
            or {}
        ).get("typelem")

    # -- Methods for building parts of the queries --
    @staticmethod
    def get_set_column_part(column: str) -> sql.Composed:
        return sql.SQL("{column} = %s").format(
            column=sql.Identifier(column),
        )

    @staticmethod
    def get_set_multiple_columns_part(
        column_names: list[str], values: list[Any]
    ) -> sql.Composed:
        return sql.SQL("({column_names}) = ({placeholders})").format(
            column_names=sql.SQL(", ").join(
                sql.Identifier(column_name) for column_name in column_names
            ),
            placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in values),
        )

    @staticmethod
    def get_transfer_from_other_table_part(
        source_collection: Collection,
        target_column_names: list[str],
        values: list[Any],
        from_migration_table: bool = False,
    ) -> sql.Composed:
        """
        Input:
            source_collection: collection with the source data
            target_column_names: names of the target table to be updated
            values: list of the values to set into the target columns. Each value can be one of:
                Plain name of the migration table
        """

        assert len(target_column_names) == len(
            values
        ), "Number of columns to update does not match the number of the new values"
        return sql.SQL("{columns_to_values} FROM {source_table}").format(
            columns_to_values=sql.SQL(", ").join(
                [
                    sql.SQL("{target_column} = {value}").format(
                        target_column=sql.Identifier(target_column),
                        value=value,
                    )
                    for target_column, value in zip(target_column_names, values)
                ]
            ),
            source_table=sql.Identifier(
                HelperGetNames.get_table_name(
                    source_collection, migration=from_migration_table
                )
            ),
        )

    @staticmethod
    def get_lookup_part_from_other_table(
        target_table_or_collection: str,
        filter_string: sql.Composable,
        source_table_or_collection: str,
        from_migration_table: bool = False,
    ) -> sql.Composed:
        return sql.SQL(
            "{target_table}.id = ANY(SELECT id FROM {source_table} WHERE {filter_string})"
        ).format(
            target_table=sql.Identifier(
                HelperGetNames.get_table_name(target_table_or_collection)
            ),
            source_table=sql.Identifier(
                HelperGetNames.get_table_name(
                    source_table_or_collection,
                    migration=from_migration_table,
                )
            ),
            filter_string=filter_string,
        )

    # -- Methods for building the queries --
    @staticmethod
    def get_update_entries_sql(
        collection_or_table_name: str,
        set_part: sql.Composable,
        condition: sql.Composable | None = None,
    ) -> sql.Composed:
        return sql.SQL("UPDATE {table} SET {set_part}{filter}").format(
            table=sql.Identifier(
                HelperGetNames.get_table_name(collection_or_table_name)
            ),
            set_part=set_part,
            filter=(
                sql.SQL(" WHERE {condition}").format(condition=condition)
                if condition
                else sql.SQL("")
            ),
        )


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

    @staticmethod
    def _get_filter_query_and_arguments(
        target_collection: Collection,
        filter_or_condition: Filter | str,
        arguments: SqlArguments,
        from_migration_table: bool | None = None,
        source_collection: str | None = None,
        table_alias: str = "",
    ) -> sql.Composable:
        """
        Builds lookup part of the SQL query.

        Helper method for functions that update entries matching the lookup expression.
        """
        filter_string: sql.Composable

        if isinstance(filter_or_condition, str):
            filter_string = sql.SQL(filter_or_condition)
        else:
            filter_string = BaseMigrationSqlHelper.build_filter_str(
                filter_or_condition, arguments, target_collection, table_alias
            )

        return (
            BaseMigrationSqlHelper.get_lookup_part_from_other_table(
                target_collection,
                filter_string,
                source_collection or target_collection,
                from_migration_table or False,
            )
            if from_migration_table is not None or source_collection is not None
            else filter_string
        )

    @staticmethod
    def update_all_entries(
        curs: Cursor[DictRow],
        collection: Collection,
        column: str,
        new_value: Any,
    ) -> None:
        """
        Sets the given value into the column for all the collection entries.

        Helper method for using in data_manipulation.
        """
        curs.execute(
            BaseMigrationSqlHelper.get_update_entries_sql(
                collection,
                BaseMigrationSqlHelper.get_set_column_part(column),
            ),
            [new_value],
        )

    @staticmethod
    def update_empty_cells(
        curs: Cursor[DictRow],
        collection: Collection,
        column: str,
        new_value: Any,
    ) -> None:
        """
        Sets the given value into the column for all the collection entries
        without the value in this column.

        Helper method for using in data_manipulation.
        """
        curs.execute(
            BaseMigrationSqlHelper.get_update_entries_sql(
                collection,
                BaseMigrationSqlHelper.get_set_column_part(column),
                sql.SQL("{column} IS NULL").format(column=sql.Identifier(column)),
            ),
            [new_value],
        )

    @staticmethod
    def update_matching_entries(
        curs: Cursor[DictRow],
        collection: Collection,
        column: str,
        new_value: Any,
        filter_or_condition: Filter | str,
        from_migration_table: bool = False,
    ) -> None:
        """
        Builds and executes mass update statement for entries that match the lookup condition.
        Input:
            cursor
            collection: name of collection to update.
            column: name of the field to update.
            filter_or_condition: Lookup expression used to select matching entries.
            from_migration_table: Determines which table the filter is applied to:
                If True: the filter is applied to the migration table.
                If False: the filter is applied to the table being modified.
            new_value: Value assigned to each entry matching the filter.

        Helper method for using in data_manipulation.
        """
        arguments: SqlArguments = [new_value]
        filter_string = BaseMigration._get_filter_query_and_arguments(
            collection, filter_or_condition, arguments, from_migration_table
        )
        curs.execute(
            BaseMigrationSqlHelper.get_update_entries_sql(
                collection,
                BaseMigrationSqlHelper.get_set_column_part(column),
                filter_string,
            ),
            arguments,
        )

    @staticmethod
    def update_matching_entries_multiple_columns(
        curs: Cursor[DictRow],
        collection: Collection,
        column_names: list[str],
        new_values: list[Any],
        filter_or_condition: Filter | str | None = None,
        from_migration_table: bool = False,
    ) -> None:
        """
        Sets the given values into the columns for all the collection entries
        that match the lookup.
        Input:
            cursor
            collection: name of collection to update.
            column_names: names of the columns to update.
            filter_or_condition: Lookup expression used to select matching entries.
                If not given or is None, all the entries will be updated.
            from_migration_table: Determines which table the filter is applied to:
                If True: the filter is applied to the migration table.
                If False: the filter is applied to the table being modified.
            new_values: Values assigned to each entry matching the filter.

        Helper method for using in data_manipulation.
        """
        assert len(column_names) == len(
            new_values
        ), f"Invalid data for collection {collection}: number of columns to update does not match the number of the new values"

        arguments: SqlArguments = [v for v in new_values]
        filter_string = BaseMigration._get_filter_query_and_arguments(
            collection, filter_or_condition or "TRUE", arguments, from_migration_table
        )
        curs.execute(
            BaseMigrationSqlHelper.get_update_entries_sql(
                collection,
                BaseMigrationSqlHelper.get_set_multiple_columns_part(
                    column_names, new_values
                ),
                filter_string,
            ),
            arguments,
        )

    @staticmethod
    def update_from_lookup_map(
        curs: Cursor[DictRow],
        collection: Collection,
        column: str,
        lookup_map: list[tuple[Filter | str, bool, Any]],
    ) -> None:
        """
        Helper method for using in data_manipulation.
        Purpose:
            Builds and executes mass update statements for each item in lookup_map.
        Input:
            cursor
            collection: name of collection to update.
            column: name of the field to update.
            lookup_map: tuple out of 3 values:
                filter_or_condition: Lookup expression used to select matching entries.
                from_migration_table: Determines which table the filter is applied to:
                    If True: the filter is applied to the migration table.
                    If False: the filter is applied to the table being modified.
                new_value: Value assigned to each entry matching the filter.
        """
        for filter_or_condition, from_migration_table, new_value in lookup_map:
            BaseMigration.update_matching_entries(
                curs,
                collection,
                column,
                new_value,
                filter_or_condition,
                from_migration_table,
            )

    @staticmethod
    def update_from_lookup_map_multiple_columns(
        curs: Cursor[DictRow],
        collection: Collection,
        columns: list[str],
        lookup_map: list[tuple[Filter | str, bool, list[Any]]],
    ) -> None:
        """
        Helper method for using in data_manipulation.
        Purpose:
            Builds and executes mass update statements for each item in lookup_map.
        Input:
            cursor
            collection: name of collection to update.
            column: name of the field to update.
            lookup_map: tuple out of 3 values:
                filter_or_condition: Lookup expression used to select matching entries.
                from_migration_table: Determines which table the filter is applied to:
                    If True: the filter is applied to the migration table.
                    If False: the filter is applied to the table being modified.
                new_value: Value assigned to each entry matching the filter.
        """
        assert all(
            [len(item[2]) == len(columns) for item in lookup_map]
        ), "Number of new values must match the number of the target columns for all the entries of lookup_map"

        for filter_or_condition, from_migration_table, new_values in lookup_map:
            BaseMigration.update_matching_entries_multiple_columns(
                curs,
                collection,
                columns,
                new_values,
                filter_or_condition,
                from_migration_table,
            )

    @staticmethod
    def update_from_mig_table_sql(
        curs: Cursor[DictRow],
        collection: str,
        target_column_names: list[str],
        values: list[Any],
        condition: sql.Composable | None = None,
    ) -> None:
        table = HelperGetNames.get_table_name(collection)
        curs.execute(
            BaseMigrationSqlHelper.get_update_entries_sql(
                table,
                set_part=BaseMigrationSqlHelper.get_transfer_from_other_table_part(
                    collection,
                    target_column_names,
                    values,
                    True,
                ),
                condition=condition
                or sql.SQL("{table}.id = {source_table}.id").format(
                    table=sql.Identifier(table),
                    source_table=sql.Identifier(
                        HelperGetNames.get_table_name(table, True)
                    ),
                ),
            )
        )
