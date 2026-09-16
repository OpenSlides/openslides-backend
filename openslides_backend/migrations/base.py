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
    def get_update_array_add_values_part(column: str, distinct: bool) -> sql.Composed:
        if distinct:
            return sql.SQL(
                "{column} = ARRAY(SELECT DISTINCT unnest(COALESCE({column}, '{{}}') || %s))"
            ).format(
                column=sql.Identifier(column),
            )
        else:
            return sql.SQL("{column} = COALESCE({column}, '{{}}') || %s").format(
                column=sql.Identifier(column),
            )

    @staticmethod
    def get_update_array_remove_values_part(
        column: str, values: list[Any]
    ) -> sql.Composable:
        expression: sql.Composable = sql.Identifier(column)
        for value in values:
            expression = sql.SQL("array_remove({expression}, %s)").format(
                expression=expression,
            )
        return sql.SQL("{column} = {expression}").format(
            column=sql.Identifier(column), expression=expression
        )

    @staticmethod
    def get_update_array_replace_values_part(
        column: str, distinct: bool
    ) -> sql.Composed:
        if distinct:
            return sql.SQL("""
                {column} = CASE
                WHEN {column} IS NULL THEN NULL
                ELSE ARRAY(
                    SELECT DISTINCT value
                    FROM unnest(array_replace({column}, %s, %s)) AS value
                )
                END
                """).format(
                column=sql.Identifier(column),
            )
        else:
            return sql.SQL("{column} = array_replace({column}, %s, %s)").format(
                column=sql.Identifier(column),
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

    @staticmethod
    def normalize_optional_condition(
        condition: sql.Composable | None,
    ) -> sql.Composable:
        return (
            sql.SQL(" WHERE {condition}").format(condition=condition)
            if condition
            else sql.SQL("")
        )

    @staticmethod
    def get_join_table_part(
        table: Table, columns: dict[Field, tuple[Table, Field]]
    ) -> sql.Composable:
        return sql.SQL(" JOIN {table} ON {columns}").format(
            table=sql.Identifier(table),
            columns=sql.SQL(" AND ").join(
                sql.SQL(
                    "{table}.{column} = {main_table_alias}.{main_table_column}"
                ).format(
                    table=sql.Identifier(table),
                    column=sql.Identifier(own_column),
                    main_table_alias=sql.Identifier(main_table_and_column[0]),
                    main_table_column=sql.Identifier(main_table_and_column[1]),
                )
                for own_column, main_table_and_column in columns.items()
            ),
        )

    @staticmethod
    def get_join_values_part(
        values: list[dict[str, str]],
        intermediate_columns: list[str],
        join_on: list[str],
        main_table_alias: str,
        values_alias: str = "v",
    ) -> sql.Composable:
        return sql.SQL(
            " JOIN (VALUES {values}) AS {values_alias}({intermediate_columns}) ON {join_on}"
        ).format(
            values=sql.SQL(", ").join(
                sql.SQL("({placeholders})").format(
                    placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in row)
                )
                for row in values
            ),
            values_alias=sql.Identifier(values_alias),
            intermediate_columns=sql.SQL(", ").join(
                sql.Identifier(column) for column in intermediate_columns
            ),
            join_on=sql.SQL(" AND ").join(
                sql.SQL("{main_table_alias}.{column} = {values_alias}.{column}").format(
                    main_table_alias=sql.Identifier(main_table_alias),
                    values_alias=sql.Identifier(values_alias),
                    column=sql.Identifier(column),
                )
                for column in join_on
            ),
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
            filter=BaseMigrationSqlHelper.normalize_optional_condition(condition),
        )

    @staticmethod
    def get_insert_from_other_table_sql(
        source_table: str,
        target_table: str,
        target_columns: list[str],
        select_list: list[tuple[str, Field]],
        join_on_part: sql.Composable | None = None,
        condition: sql.Composable | None = None,
        return_fields: list[str] = ["id"],
    ) -> sql.Composed:
        """
        transfer_from_source: map of the columns that should be transfered from the source table
        where source and target columns have different names:
            * key: column name in the target table into which the value will be inserted
            * value: column in the source table from which the value will be taken
        """

        return sql.SQL("""
            INSERT INTO {target_table} ({target_columns})
            SELECT {select_list}
            FROM {source_table} {join_on_part}{filter}
            RETURNING {return_fields};
        """).format(
            target_table=sql.Identifier(target_table),
            target_columns=sql.SQL(", ").join(
                sql.Identifier(column) for column in target_columns
            ),
            select_list=sql.SQL(", ").join(
                sql.SQL("{table_alias}.{column}").format(
                    table_alias=sql.Identifier(item[0]),
                    column=sql.Identifier(item[1]),
                )
                for item in select_list
            ),
            source_table=sql.Identifier(source_table),
            join_on_part=join_on_part,
            filter=BaseMigrationSqlHelper.normalize_optional_condition(condition),
            return_fields=sql.SQL(", ").join(sql.SQL(field) for field in return_fields),
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
    def update_from_mig_table(
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

    @staticmethod
    def update_from_other_table(
        curs: Cursor[DictRow],
        target_collection: Collection,
        target_column_names: list[str],
        source_collection: Collection,
        from_migration_table: bool,
        values: list[Any],
        match_condition: Filter | str,
        filter_source_table: Filter | str | None = None,
        filter_target_table: Filter | str | None = None,
    ) -> None:
        target_table = HelperGetNames.get_table_name(target_collection)
        source_table = HelperGetNames.get_table_name(
            source_collection, from_migration_table
        )
        filter_arguments: SqlArguments = []
        filters: list[sql.Composable] = []
        if isinstance(match_condition, str):
            filters.append(
                BaseMigration._get_filter_query_and_arguments(
                    target_collection, match_condition, filter_arguments
                )
            )
        else:
            filters.append(
                BaseMigration._get_filter_query_and_arguments(
                    target_collection,
                    match_condition,
                    filter_arguments,
                    from_migration_table,
                    source_collection,
                )
            )

        for filter_or_condition, table in [
            (filter_source_table, source_table),
            (filter_target_table, target_table),
        ]:
            if filter_or_condition is not None:
                filters.append(
                    BaseMigration._get_filter_query_and_arguments(
                        target_collection,
                        filter_or_condition,
                        filter_arguments,
                        table_alias=table,
                    ),
                )

        curs.execute(
            BaseMigrationSqlHelper.get_update_entries_sql(
                target_table,
                set_part=BaseMigrationSqlHelper.get_transfer_from_other_table_part(
                    source_collection,
                    target_column_names,
                    values,
                    from_migration_table,
                ),
                condition=sql.SQL(" AND ").join(filters),
            )
        )

    @staticmethod
    def update_array(
        curs: Cursor[DictRow],
        collection: str,
        column: str,
        add: list[Any] = [],
        remove: list[Any] = [],
        replace: dict[Any, Any] = {},
        dictinct: bool = True,
        filter_or_condition: Filter | str | None = None,
    ) -> None:
        filter_arguments: SqlArguments = []
        condition: sql.Composable | None = (
            BaseMigration._get_filter_query_and_arguments(
                collection, filter_or_condition, filter_arguments
            )
            if filter_or_condition
            else None
        )

        if add:
            BaseMigration._handle_update_array_add(
                curs, collection, column, add, condition, filter_arguments, dictinct
            )

        if remove:
            BaseMigration._handle_update_array_remove(
                curs, collection, column, remove, condition, filter_arguments
            )

        if replace:
            BaseMigration._handle_update_array_replace(
                curs, collection, column, replace, condition, filter_arguments, dictinct
            )

    @staticmethod
    def _handle_update_array_add(
        curs: Cursor[DictRow],
        collection: str,
        column: str,
        add: list[Any],
        condition: sql.Composable | None,
        filter_arguments: SqlArguments,
        distinct: bool,
    ) -> None:
        curs.execute(
            BaseMigrationSqlHelper.get_update_entries_sql(
                collection,
                BaseMigrationSqlHelper.get_update_array_add_values_part(
                    column, distinct
                ),
                condition,
            ),
            [add, *filter_arguments],
        )

    @staticmethod
    def _handle_update_array_remove(
        curs: Cursor[DictRow],
        collection: str,
        column: str,
        remove: list[Any],
        condition: sql.Composable | None,
        filter_arguments: SqlArguments,
    ) -> None:
        curs.execute(
            BaseMigrationSqlHelper.get_update_entries_sql(
                collection,
                BaseMigrationSqlHelper.get_update_array_remove_values_part(
                    column, remove
                ),
                condition,
            ),
            [*remove, *filter_arguments],
        )

    @staticmethod
    def _handle_update_array_replace(
        curs: Cursor[DictRow],
        collection: str,
        column: str,
        replace: dict[Any, Any],
        condition: sql.Composable | None,
        filter_arguments: SqlArguments,
        distinct: bool,
    ) -> None:
        for old, new in replace.items():
            curs.execute(
                BaseMigrationSqlHelper.get_update_entries_sql(
                    collection,
                    BaseMigrationSqlHelper.get_update_array_replace_values_part(
                        column, distinct
                    ),
                    condition,
                ),
                [old, new, *filter_arguments],
            )

    @staticmethod
    def insert_from_other_table(
        curs: Cursor[DictRow],
        target_collection: str,
        main_source_table: str,
        additional_souce_tables: dict[Table, dict[Field, tuple[Table, Field]]] = {},
        copy_from_source_tables: dict[Table, dict[Field, Field]] = {},
        generate_from_map: list[dict[Field, Any]] = [],
        values_join_on: list[Field] = [],
        filter_or_condition: Filter | str | None = None,
        return_fields: list[str] = [],
    ) -> list[int]:
        """
        transfer_from_source_table: map of the columns that should be transfered from the source table
        where source and target columns have different names:
            * key: column name in the target table into which the value will be inserted
            * value: column in the source table from which the value will be taken
        """
        join_on_parts: list[sql.Composable] = []
        if generate_from_map:
            assert (
                values_join_on
            ), "'generate_from_map' must be used only together with 'values_join_on'."
            intermediate_columns = list(generate_from_map[0].keys())
            assert all(
                [
                    set(generate_from_map[i]) == set(intermediate_columns)
                    for i in range(1, len(generate_from_map))
                ]
            ), "All dictionaries in 'generate_from_map' must have the same keys."
            join_on_parts.append(
                BaseMigrationSqlHelper.get_join_values_part(
                    generate_from_map,
                    intermediate_columns,
                    values_join_on,
                    main_source_table,
                )
            )
        else:
            intermediate_columns = []

        for table, join_on_columns in additional_souce_tables.items():
            join_on_parts.append(
                BaseMigrationSqlHelper.get_join_table_part(table, join_on_columns)
            )

        target_columns: list[str] = [
            column for column in intermediate_columns if column not in values_join_on
        ]
        select_list: list[tuple[str, Field]] = [
            ("v", column) for column in target_columns
        ]
        for table, columns in copy_from_source_tables.items():
            target_columns.extend(columns.values())
            select_list.extend([(table, column) for column in columns.keys()])

        arguments: SqlArguments = [
            row[column_name]
            for row in generate_from_map
            for column_name in intermediate_columns
        ]
        condition: sql.Composable | None = (
            BaseMigration._get_filter_query_and_arguments(
                target_collection, filter_or_condition, arguments
            )
            if filter_or_condition
            else None
        )
        curs.execute(
            BaseMigrationSqlHelper.get_insert_from_other_table_sql(
                source_table=main_source_table,
                target_table=HelperGetNames.get_table_name(target_collection),
                target_columns=target_columns,
                select_list=select_list,
                join_on_part=sql.SQL(" ").join(join_on_parts),
                condition=condition,
                return_fields=return_fields,
            ),
            arguments,
        )
        return [item["id"] for item in curs.fetchall()]
