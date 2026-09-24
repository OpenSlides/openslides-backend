from collections import Counter
from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.alter_schema_helper import AlterSchemaHelper
from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.patterns import (
    Column,
    ExtendedSqlArguments,
    Join,
    JoinOn,
    Renames,
    Table,
    ValuesSource,
    View,
)
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.filters import BaseSqlQueryHelper, Filter, SqlArguments
from openslides_backend.shared.patterns import Collection, Field


class BaseMigrationSqlHelper(BaseSqlQueryHelper):
    # -- Override not implemented parent method --
    @staticmethod
    def get_array_type(
        collection: Collection, field: Field, curs: Cursor[DictRow]
    ) -> sql.Composable:
        result = (
            curs.execute(
                sql.SQL("""
                    SELECT
                        element_type.typname AS element_type_name
                    FROM pg_attribute AS a
                    JOIN pg_type AS array_type
                        ON array_type.oid = a.atttypid
                    JOIN pg_type AS element_type
                        ON element_type.oid = array_type.typelem
                    WHERE a.attrelid = {table_name}::regclass
                    AND a.attname = {column_name}
                    """).format(
                    table_name=HelperGetNames.get_table_name(collection),
                    column_name=field,
                )
            ).fetchone()
            or {}
        )
        if element_type_name := result.get("element_type_name"):
            return sql.SQL(f"::{element_type_name}[]")
        raise BadCodingException(f"{collection}/{field} is not an array column.")

    # -- Methods for building SET part --
    @staticmethod
    def get_set_columns_part(
        new_values: dict[Column, Any], arguments: SqlArguments
    ) -> sql.Composed:
        if not new_values:
            raise BadCodingException("column_names must not be empty")

        columns = list(new_values.keys())
        values = list(new_values.values())
        arguments.extend(values)

        if len(columns) == 1:
            return sql.SQL("{column} = {placeholder}").format(
                column=sql.Identifier(columns[0]),
                placeholder=sql.Placeholder(),
            )

        return sql.SQL("({column_names}) = ({placeholders})").format(
            column_names=sql.SQL(", ").join(
                sql.Identifier(column) for column in columns
            ),
            placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in values),
        )

    @staticmethod
    def _build_identifier(
        qualifier: str | None,
        column: Column,
    ) -> sql.Identifier:
        if qualifier is None:
            return sql.Identifier(column)

        return sql.Identifier(qualifier, column)

    @staticmethod
    def get_column_assignment(
        target_column: Column,
        target_table: str | None = None,
        source_column: Column | None = None,
        source_qualifier: str | None = None,
    ) -> sql.Composed:
        if source_column is None:
            source_column = target_column
        return sql.SQL("{target} = {source}").format(
            target=BaseMigrationSqlHelper._build_identifier(
                target_table, target_column
            ),
            source=BaseMigrationSqlHelper._build_identifier(
                source_qualifier, source_column
            ),
        )

    @staticmethod
    def build_array_source_expression(
        column: Column,
        replace: dict[Any, Any] | None,
        arguments: ExtendedSqlArguments,
        array_type: sql.Composable,
    ) -> sql.Composed:
        expression = sql.SQL("COALESCE({column}, ARRAY[]{array_type})").format(
            column=sql.Identifier(column), array_type=array_type
        )
        if replace:
            for old, new in replace.items():
                expression = sql.SQL(
                    "array_replace({expression}, {old_value}, {new_value})"
                ).format(
                    expression=expression,
                    old_value=sql.Placeholder(),
                    new_value=sql.Placeholder(),
                )
                arguments.extend([old, new])
        return expression

    @staticmethod
    def build_array_remove_expression(
        remove: set[Any] | None,
        arguments: ExtendedSqlArguments,
        array_type: sql.Composable,
    ) -> sql.Composable:
        if not remove:
            return sql.SQL("")
        arguments.append(sorted(remove))
        return sql.SQL("EXCEPT SELECT unnest({remove}{array_type})").format(
            remove=sql.Placeholder(), array_type=array_type
        )

    @staticmethod
    def build_array_add_expression(
        add: set[Any] | None,
        arguments: ExtendedSqlArguments,
        array_type: sql.Composable,
    ) -> sql.Composable:
        if not add:
            return sql.SQL("")
        arguments.append(sorted(add))
        return sql.SQL("UNION SELECT unnest({add}{array_type})").format(
            add=sql.Placeholder(), array_type=array_type
        )

    @staticmethod
    def build_array_update_part(
        column: Column,
        array_type: sql.Composable,
        source: sql.Composable,
        add: sql.Composable,
        remove: sql.Composable,
    ) -> sql.Composed:
        return sql.SQL("""
            {column} = NULLIF(
                ARRAY(
                    SELECT DISTINCT list_element FROM (
                        SELECT unnest({source}) AS list_element
                        {remove}
                        {add}

                    ) AS elements
                    ORDER BY list_element
                ),
                ARRAY[]{array_type}
            )
            """).format(
            column=sql.Identifier(column),
            source=source,
            remove=remove,
            add=add,
            array_type=array_type,
        )

    # -- Methods for building WHERE part --
    @staticmethod
    def get_lookup_part_from_other_table(
        target_table: Table,
        source_table: Table | View,
        filter_string: sql.Composable,
    ) -> sql.Composed:
        return sql.SQL(
            "EXISTS (SELECT 1 FROM {source_table} WHERE {source_table}.id = {target_table}.id AND ({filter_string}))"
        ).format(
            target_table=sql.Identifier(target_table),
            source_table=sql.Identifier(source_table),
            filter_string=filter_string,
        )

    # -- Methods for building FROM part --
    @staticmethod
    def build_values_table(
        values_source: ValuesSource,
        arguments: SqlArguments,
    ) -> sql.Composed:
        arguments.extend(
            row[column]
            for row in values_source.rows
            for column in values_source.columns
        )
        return sql.SQL("(VALUES {values}) AS {alias}({columns})").format(
            values=sql.SQL(", ").join(
                sql.SQL("({placeholders})").format(
                    placeholders=sql.SQL(", ").join(
                        sql.Placeholder() * len(values_source.columns)
                    )
                )
                for _ in values_source.rows
            ),
            alias=sql.Identifier(values_source.alias),
            columns=sql.SQL(", ").join(
                sql.Identifier(column) for column in values_source.columns
            ),
        )

    @staticmethod
    def get_join_conditions(
        right_table: str, join_on_columns: list[JoinOn]
    ) -> list[sql.Composable]:
        return [
            sql.SQL("{left_table}.{left_column} = {right_table}.{right_column}").format(
                right_table=sql.Identifier(right_table),
                right_column=sql.Identifier(join_on.right_column),
                left_table=sql.Identifier(join_on.left_table),
                left_column=sql.Identifier(join_on.left_column),
            )
            for join_on in join_on_columns
        ]

    @staticmethod
    def get_join_conditions_for_values(
        values_source: ValuesSource,
        left_table: Table | View,
    ) -> list[sql.Composable]:
        return BaseMigrationSqlHelper.get_join_conditions(
            values_source.alias,
            [JoinOn(column, (left_table, column)) for column in values_source.join_on],
        )

    @staticmethod
    def get_join_table_part(join_table: Join, arguments: SqlArguments) -> sql.Composed:
        conditions: list[sql.Composable] = BaseMigrationSqlHelper.get_join_conditions(
            join_table.table, join_table.join_on
        )

        if join_table.filter is not None:
            conditions.append(
                BaseMigration._build_filter_query(
                    join_table.collection,
                    join_table.filter,
                    arguments,
                    join_table.table,
                )
            )

        return sql.SQL("JOIN {right_table} ON {conditions}").format(
            right_table=sql.Identifier(join_table.table),
            conditions=sql.SQL(" AND ").join(
                sql.SQL("({condition})").format(condition=condition)
                for condition in conditions
            ),
        )

    @staticmethod
    def get_join_values_part(
        values_source: ValuesSource,
        left_table: Table | View,
        arguments: SqlArguments,
    ) -> sql.Composed:
        return sql.SQL("JOIN {values} ON {columns}").format(
            values=BaseMigrationSqlHelper.build_values_table(values_source, arguments),
            columns=sql.SQL(" AND ").join(
                BaseMigrationSqlHelper.get_join_conditions_for_values(
                    values_source, left_table
                )
            ),
        )

    @staticmethod
    def build_source_columns_map(
        copy_from_source_tables: dict[
            Table | View,
            dict[Column, Column | sql.Composed],
        ],
    ) -> dict[Column, sql.Composable]:
        return {
            target_column: (
                source_value
                if isinstance(source_value, sql.Composed)
                else sql.Identifier(source_table, source_value)
            )
            for source_table, values in copy_from_source_tables.items()
            for target_column, source_value in values.items()
        }

    # -- Methods for building the queries --
    @staticmethod
    def normalize_from(from_part: sql.Composable | None) -> sql.Composable:
        if from_part is None:
            return sql.SQL("")
        return sql.SQL(" FROM {from_part}").format(from_part=from_part)

    @staticmethod
    def normalize_filter(
        condition: sql.Composable | list[sql.Composable] | None,
    ) -> sql.Composable:
        if condition is None:
            return sql.SQL("")
        if isinstance(condition, list):
            if not condition:
                raise BadCodingException("Filter condition list must not be empty")
            condition = sql.SQL(" AND ").join(
                sql.SQL("({filter_str})").format(filter_str=line) for line in condition
            )
        return sql.SQL(" WHERE {condition}").format(condition=condition)

    @staticmethod
    def build_update_entries_sql(
        collection_or_table_name: str,
        set_part: sql.Composable,
        where_part: sql.Composable | list[sql.Composable] | None = None,
        from_part: sql.Composable | None = None,
    ) -> sql.Composed:
        return sql.SQL("UPDATE {target_table} SET {set_part}{from_part}{where}").format(
            target_table=sql.Identifier(
                HelperGetNames.get_table_name(collection_or_table_name)
            ),
            set_part=set_part,
            from_part=BaseMigrationSqlHelper.normalize_from(from_part),
            where=BaseMigrationSqlHelper.normalize_filter(where_part),
        )

    @staticmethod
    def build_insert_from_other_table_sql(
        source_table: Table | View,
        target_table: Table,
        target_columns: sql.Composed,
        select_list: sql.Composed,
        joined_tables: list[sql.Composable],
        condition: sql.Composable | None = None,
        return_fields: list[str] | None = None,
    ) -> sql.Composed:
        """
        transfer_from_source: map of the columns that should be transfered from the source table
        where source and target columns have different names:
            * key: column name in the target table into which the value will be inserted
            * value: column in the source table from which the value will be taken
        """

        return sql.SQL(
            "INSERT INTO {target_table} ({target_columns}) "
            "SELECT {select_list} "
            "FROM {source_table}"
            "{joined_tables}"
            "{where}"
            "{returning}"
        ).format(
            target_table=sql.Identifier(target_table),
            target_columns=target_columns,
            select_list=select_list,
            source_table=sql.Identifier(source_table),
            joined_tables=(
                sql.SQL(" ") + sql.SQL(" ").join(joined_tables)
                if joined_tables
                else sql.SQL("")
            ),
            where=BaseMigrationSqlHelper.normalize_filter(condition),
            returning=(
                sql.SQL(" RETURNING {return_fields}").format(
                    return_fields=sql.SQL(", ").join(
                        sql.Identifier(field) for field in return_fields
                    )
                )
                if return_fields
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
    def _build_filter_query(
        target_collection: Collection,
        filter_condition: Filter,
        arguments: SqlArguments,
        filter_condition_table_alias: str | None = None,
        filter_other_table: Table | View | None = None,
    ) -> sql.Composable:
        """
        Builds lookup part of the SQL query. Also updates arguments.

        Helper method for functions that update entries matching the lookup expression.
        """
        filter_string = BaseMigrationSqlHelper.build_filter_str(
            filter_condition,
            arguments,
            target_collection,
            filter_condition_table_alias or "",
        )
        return (
            BaseMigrationSqlHelper.get_lookup_part_from_other_table(
                HelperGetNames.get_table_name(target_collection),
                filter_other_table,
                filter_string,
            )
            if filter_other_table is not None
            else filter_string
        )

    # -- Helpers for data_manipulation --
    @staticmethod
    def _base_update_entries(
        curs: Cursor[DictRow],
        collection: Collection,
        new_values: dict[Column, Any],
        filter_condition: Filter | None = None,
        apply_filter_to_migration_table: bool | None = None,
    ) -> None:
        """
        Builds and executes mass update statement for entries that match the lookup condition.
        Input:
            cursor
            collection: name of collection to update.
            column_names: names of the columns to update.
            new_values: Values assigned to each entry matching the filter.
            filter_condition: Lookup expression used to select matching entries.
            apply_filter_to_migration_table: Determines which table the filter is applied to:
                If True: the filter is applied to the migration table.
                If False: the filter is applied to the table being modified.
        """
        arguments: SqlArguments = []
        query = BaseMigrationSqlHelper.build_update_entries_sql(
            collection_or_table_name=collection,
            set_part=BaseMigrationSqlHelper.get_set_columns_part(new_values, arguments),
            where_part=(
                BaseMigration._build_filter_query(
                    target_collection=collection,
                    filter_condition=filter_condition,
                    arguments=arguments,
                    filter_other_table=(
                        HelperGetNames.get_table_name(
                            collection, migration=apply_filter_to_migration_table
                        )
                        if apply_filter_to_migration_table is not None
                        else None
                    ),
                )
                if filter_condition is not None
                else None
            ),
        )
        curs.execute(query, arguments)

    @staticmethod
    def update_all_entries(
        curs: Cursor[DictRow],
        collection: Collection,
        new_values: dict[Column, Any],
    ) -> None:
        """
        Sets the given simple value into the column for all the collection entries.
        """
        BaseMigration._base_update_entries(curs, collection, new_values)

    @staticmethod
    def update_matching_entries(
        curs: Cursor[DictRow],
        collection: Collection,
        new_values: dict[Column, Any],
        filter_condition: Filter,
        apply_filter_to_migration_table: bool | None = None,
    ) -> None:
        """
        Builds and executes mass update statement for entries that match the lookup condition.
        """
        BaseMigration._base_update_entries(
            curs,
            collection,
            new_values,
            filter_condition,
            apply_filter_to_migration_table or None,
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
            BaseMigrationSqlHelper.build_update_entries_sql(
                collection,
                BaseMigrationSqlHelper.get_set_columns_part(
                    {column: new_value}, arguments
                ),
                sql.SQL("{column} IS NULL").format(column=sql.Identifier(column)),
            ),
            arguments,
        )

    @staticmethod
    def _validate_values_map(
        values_map: list[dict[Column, Any]], join_values_on_columns: list[Column]
    ) -> ValuesSource:
        errors = []
        if not values_map:
            errors.append("values_map must not be empty.")
        if not join_values_on_columns:
            errors.append("join_on_fields must not be empty.")
        if errors:
            raise BadCodingException("\n".join(errors))

        values_columns = list(values_map[0].keys())
        values_column_set = set(values_columns)
        join_column_set = set(join_values_on_columns)
        if len(join_values_on_columns) != len(join_column_set):
            errors.append("join_columns must not contain duplicates.")

        if values_column_set == join_column_set:
            errors.append(
                "Dictionaries from values_map must contain columns "
                "other than join_on_fields."
            )
        elif not join_column_set.issubset(values_column_set):
            errors.append(
                "Dictionaries from values_map must include all the "
                "values from join_on_fields."
            )

        if not all(set(row) == values_column_set for row in values_map[1:]):
            errors.append("All dictionaries in 'values_map' must have the same keys.")

        if errors:
            raise BadCodingException("\n".join(errors))

        return ValuesSource(
            columns=values_columns,
            rows=values_map,
            join_on=join_values_on_columns,
        )

    @staticmethod
    def update_from_values_map(
        curs: Cursor[DictRow],
        target_collection: Collection,
        values_map: list[dict[Column, Any]],
        join_values_on_columns: list[Column],
        filter_condition: Filter | None = None,
    ) -> None:
        """
        Builds and executes mass update statements for each item in lookup_map.

        Keys in all dictionaries must be the same.
        """
        values_source = BaseMigration._validate_values_map(
            values_map, join_values_on_columns
        )

        arguments: SqlArguments = []
        target_table = HelperGetNames.get_table_name(target_collection)

        target_columns = [
            column
            for column in values_source.columns
            if column not in values_source.join_on
        ]

        set_part = sql.SQL(", ").join(
            BaseMigrationSqlHelper.get_column_assignment(
                target_column=column,
                source_qualifier=values_source.alias,
            )
            for column in target_columns
        )
        from_part = BaseMigrationSqlHelper.build_values_table(values_source, arguments)
        join_conditions = BaseMigrationSqlHelper.get_join_conditions_for_values(
            values_source, target_table
        )
        filter_conditions = (
            [
                BaseMigration._build_filter_query(
                    target_collection, filter_condition, arguments
                )
            ]
            if filter_condition is not None
            else []
        )
        curs.execute(
            BaseMigrationSqlHelper.build_update_entries_sql(
                collection_or_table_name=target_table,
                set_part=set_part,
                from_part=from_part,
                where_part=[*join_conditions, *filter_conditions],
            ),
            arguments,
        )

    @staticmethod
    def _validate_source_tables_data(
        main_source: Table | View,
        join_to_target_table: bool,
        source_tables: list[Join] | None,
        copy_from_source_tables: dict[
            Table | View, dict[Column, Column | sql.Composed]
        ],
    ) -> None:
        """
        source_tables: {right_table: {right_column: (left_table, left_column)}}
        copy_from_source_tables: {source_table: {target_column: source_column | value built from source_column}}
        """
        errors = []

        # Check no empty dicts
        if source_tables and (
            empty_inner_join_on := [
                source_table.table
                for source_table in source_tables
                if not source_table.join_on
            ]
        ):
            errors.append(
                "'source_tables' contains empty list(s) in join_on: "
                f"{', '.join(map(str, empty_inner_join_on))}."
            )
        if not copy_from_source_tables:
            errors.append("'copy_from_source_tables' must not be empty.")
        elif empty_inner_dicts := [
            table for table, values in copy_from_source_tables.items() if not values
        ]:
            errors.append(
                "'copy_from_source_tables' contains empty dictionary(s): "
                f"{', '.join(map(str, empty_inner_dicts))}."
            )

        # Check one source per target column
        if copy_from_source_tables:
            target_columns = [
                column for data in copy_from_source_tables.values() for column in data
            ]
            if duplicates := [
                column for column, count in Counter(target_columns).items() if count > 1
            ]:
                errors.append(
                    f"copy_from_source_tables defines multiple sources for column(s): {duplicates}"
                )

        # Check same source tables/views in both dictionaries
        if source_tables and copy_from_source_tables:
            source_table_set = {source_table.table for source_table in source_tables}
            copy_source_table_set = set(copy_from_source_tables)

            if unused := (source_table_set - copy_source_table_set):
                errors.append(
                    f"Source(s) from source_tables are not used in copy_from_source_tables: {unused}."
                )
            if undefined := (copy_source_table_set - source_table_set):
                errors.append(
                    f"Source(s) from copy_from_source_tables are not defined in source_tables: {undefined}."
                )

        # Check join tree
        if source_tables:
            root_source = next(iter(source_tables))
            if [
                left_table
                for join_on_data in root_source.join_on
                if (left_table := join_on_data.left_table) != main_source
            ]:
                if join_to_target_table:
                    errors.append(
                        "Root table from source_tables must join to the target_table."
                    )
                else:
                    errors.append(
                        "Root table from additional_source_tables must join to the main_source_table."
                    )
            else:
                seen_sources = {main_source}

                for source_table in source_tables[1:]:
                    right_table = source_table.table
                    for join_on_data in source_table.join_on:
                        if right_table == (left_table := join_on_data.left_table):
                            errors.append(f"Can not join {right_table} to itself.")
                        elif left_table not in seen_sources:
                            errors.append(
                                f"Can not join {right_table} to {left_table} because {left_table} has to be joined first."
                            )
                    seen_sources.add(right_table)

        if errors:
            raise BadCodingException("\n".join(errors))

    @staticmethod
    def update_from_mig_table(
        curs: Cursor[DictRow],
        collection: Collection,
        copy_from_source_table: dict[Column, Column | sql.Composed],
        filter_target_table: Filter | None = None,
    ) -> None:
        target_table = HelperGetNames.get_table_name(collection)
        source_table = HelperGetNames.get_table_name(collection, True)
        BaseMigration.update_from_other_table(
            curs,
            collection,
            [Join(source_table, [JoinOn("id", (target_table, "id"))])],
            {source_table: copy_from_source_table},
            filter_target_table,
        )

    @staticmethod
    def update_from_other_table(
        curs: Cursor[DictRow],
        target_collection: Collection,
        source_tables: list[Join],
        copy_from_source_tables: dict[
            Table | View, dict[Column, Column | sql.Composed]
        ],
        filter_target_table: Filter | None = None,
    ) -> None:
        target_table = HelperGetNames.get_table_name(target_collection)
        BaseMigration._validate_source_tables_data(
            target_table, True, source_tables, copy_from_source_tables
        )
        joined_tables_parts: list[sql.Composable] = []
        filters: list[sql.Composable] = []
        arguments: SqlArguments = []
        for i, source_table in enumerate(source_tables):
            if i == 0:
                main_source_table = source_table.table
                filters.extend(
                    BaseMigrationSqlHelper.get_join_conditions(
                        main_source_table, source_table.join_on
                    )
                )
                if source_table.filter is not None:
                    filters.append(
                        BaseMigration._build_filter_query(
                            target_collection,
                            source_table.filter,
                            arguments,
                            filter_condition_table_alias=main_source_table,
                        )
                    )
            else:
                joined_tables_parts.append(
                    BaseMigrationSqlHelper.get_join_table_part(source_table, arguments)
                )
        if filter_target_table:
            filters.append(
                BaseMigration._build_filter_query(
                    target_collection,
                    filter_target_table,
                    arguments,
                    filter_condition_table_alias=target_table,
                )
            )

        source_columns_map = BaseMigrationSqlHelper.build_source_columns_map(
            copy_from_source_tables
        )

        curs.execute(
            BaseMigrationSqlHelper.build_update_entries_sql(
                collection_or_table_name=target_table,
                set_part=sql.SQL(", ").join(
                    sql.SQL("{target_column} = {value}").format(
                        target_column=sql.Identifier(target_column),
                        value=value,
                    )
                    for target_column, value in source_columns_map.items()
                ),
                from_part=sql.SQL("{source_table}{joined_tables}").format(
                    source_table=sql.Identifier(main_source_table),
                    joined_tables=(
                        sql.SQL(" ").join(joined_tables_parts)
                        if joined_tables_parts
                        else sql.SQL("")
                    ),
                ),
                where_part=filters,
            ),
            arguments,
        )

    @staticmethod
    def _validate_update_array_arguments(
        add: set[Any] | None,
        remove: set[Any] | None,
        replace: dict[Any, Any] | None,
    ) -> None:
        if not add and not remove and not replace:
            raise BadCodingException(
                "update_array must have at least one of 'add', 'remove' or 'replace' parameters provided."
            )
        replace_dict = replace or {}
        if (
            len(
                {
                    type(item)
                    for item in [
                        *(add or []),
                        *(remove or []),
                        *replace_dict.keys(),
                        *replace_dict.values(),
                    ]
                }
            )
            > 1
        ):
            raise BadCodingException(
                "All values in add, remove and replace must have the same type."
            )

        errors: list[str] = []
        overlaps: list[tuple[str, str, set[Any]]] = []

        if add and remove and (overlap := add & remove):
            overlaps.append(("add", "remove", overlap))
        if replace:
            replace_keys = set(replace.keys())
            replace_values = set(replace.values())
            for parameter, values in [("add", add), ("remove", remove)]:
                if values and (overlap := values & replace_keys):
                    overlaps.append((parameter, "replace keys", overlap))
            if overlap := replace_keys & replace_values:
                overlaps.append(("replace keys", "replace values", overlap))
            for old, new in replace.items():
                if old == new:
                    errors.append(f"Replacement value cannot be identical: {old}")

        for parameter1, parameter2, values in overlaps:
            errors.append(
                f"{parameter1} and {parameter2} should not have the same values within one update_array call. Duplicate values: {sorted(list(values))}."
            )
        if errors:
            raise BadCodingException("\n".join(errors))

    @staticmethod
    def update_array(
        curs: Cursor[DictRow],
        collection: str,
        column: Column,
        add: set[Any] | None = None,
        remove: set[Any] | None = None,
        replace: dict[Any, Any] | None = None,
        filter_condition: Filter | None = None,
    ) -> None:
        """
        Updates an array column using add/remove/replace operations.

        The resulting array contains unique values sorted in ascending order.
        """
        BaseMigration._validate_update_array_arguments(add, remove, replace)
        filter_arguments: SqlArguments = []
        values_arguments: ExtendedSqlArguments = []
        array_type = BaseMigrationSqlHelper.get_array_type(collection, column, curs)

        curs.execute(
            BaseMigrationSqlHelper.build_update_entries_sql(
                collection_or_table_name=collection,
                set_part=BaseMigrationSqlHelper.build_array_update_part(
                    column=column,
                    array_type=array_type,
                    source=BaseMigrationSqlHelper.build_array_source_expression(
                        column, replace, values_arguments, array_type
                    ),
                    remove=BaseMigrationSqlHelper.build_array_remove_expression(
                        remove, values_arguments, array_type
                    ),
                    add=BaseMigrationSqlHelper.build_array_add_expression(
                        add, values_arguments, array_type
                    ),
                ),
                where_part=(
                    BaseMigration._build_filter_query(
                        collection, filter_condition, filter_arguments
                    )
                    if filter_condition is not None
                    else None
                ),
            ),
            [*values_arguments, *filter_arguments],
        )

    @staticmethod
    def _validate_optional_data_sources(
        main_source_table: Table | View | None,
        additional_source_tables: list[Join] | None,
        copy_from_source_tables: (
            dict[
                Table | View,
                dict[Column, Column | sql.Composed],
            ]
            | None
        ),
        values_map: list[dict[Column, Any]] | None,
        join_values_on_columns: list[Column] | None,
        filter_main_source_table: Filter | None,
    ) -> tuple[Table | View, ValuesSource | None]:
        values_source = None
        if copy_from_source_tables is not None:
            if len(copy_from_source_tables) == 1 and main_source_table is None:
                main_source_table = list(copy_from_source_tables.keys())[0]
            elif len(copy_from_source_tables) > 1 and (
                main_source_table is None or not additional_source_tables
            ):
                raise BadCodingException(
                    "'copy_from_source_tables' with more than 1 sorce can not be used without 'main_source_table' and 'additional_source_tables'."
                )
        elif filter_main_source_table is not None:
            raise BadCodingException(
                "'filter_main_source_table' can not be used without 'copy_from_source_tables'."
            )
        assert main_source_table is not None
        if copy_from_source_tables is not None:
            BaseMigration._validate_source_tables_data(
                main_source_table,
                False,
                additional_source_tables,
                copy_from_source_tables,
            )
        if values_map is not None:
            if join_values_on_columns is None:
                raise BadCodingException(
                    "'values_map' can not be used without 'join_values_on_columns'."
                )
            else:
                values_source = BaseMigration._validate_values_map(
                    values_map, join_values_on_columns
                )
        return main_source_table, values_source

    @staticmethod
    def insert_from_other_table(
        curs: Cursor[DictRow],
        target_collection: Collection,
        main_source_table: Table | View | None = None,
        additional_source_tables: list[Join] | None = None,
        copy_from_source_tables: (
            dict[
                Table | View,
                dict[Column, Column | sql.Composed],
            ]
            | None
        ) = None,
        values_map: list[dict[Column, Any]] | None = None,
        join_values_on_columns: list[Column] | None = None,
        filter_main_source_table: Filter | None = None,
        return_fields: list[str] = [],
    ) -> dict[int, dict[str, Any]]:
        """
        Inserts values selected from one or more sources.

        If 'copy_from_source_tables' contains more than 1 table, 'main_source_table'
        and 'additional_source_tables' must be defined.

        copy_from_source_tables:
            {
                source_table: {
                    target_column: source_column | SQL expression
                }
            }

        values_map can additionally provide a map of values to set - list
        of dictionaries with 2 types of keys:
            * Columns to define the matching entries in which new values sould
              be inserted. Must be defined in join_values_on_columns.
            * Columns that should be updated.
        """
        target_table = HelperGetNames.get_table_name(target_collection)
        main_source_table, values_source = (
            BaseMigration._validate_optional_data_sources(
                main_source_table,
                additional_source_tables,
                copy_from_source_tables,
                values_map,
                join_values_on_columns,
                filter_main_source_table,
            )
        )

        arguments: SqlArguments = []
        joined_tables_parts: list[sql.Composable] = []
        target_columns: list[Column] = []
        select_list: list[sql.Composable] = []

        if copy_from_source_tables:
            source_columns_map = BaseMigrationSqlHelper.build_source_columns_map(
                copy_from_source_tables
            )
            target_columns.extend(list(source_columns_map.keys()))
            select_list.extend(list(source_columns_map.values()))

        if values_source is not None:
            joined_tables_parts.append(
                BaseMigrationSqlHelper.get_join_values_part(
                    values_source, main_source_table, arguments
                )
            )
            values_columns = [
                column
                for column in values_source.columns
                if column not in values_source.join_on
            ]

            target_columns.extend(values_columns)
            select_list.extend(
                sql.Identifier(values_source.alias, column) for column in values_columns
            )
        if additional_source_tables:
            for source_table in additional_source_tables:
                joined_tables_parts.append(
                    BaseMigrationSqlHelper.get_join_table_part(source_table, arguments)
                )
        filter_condition = (
            BaseMigration._build_filter_query(
                target_collection,
                filter_main_source_table,
                arguments,
                filter_condition_table_alias=main_source_table,
            )
            if filter_main_source_table
            else None
        )
        curs.execute(
            BaseMigrationSqlHelper.build_insert_from_other_table_sql(
                source_table=main_source_table,
                target_table=target_table,
                target_columns=sql.SQL(", ").join(
                    sql.Identifier(column) for column in target_columns
                ),
                select_list=sql.SQL(", ").join(select_list),
                joined_tables=joined_tables_parts,
                condition=filter_condition,
                return_fields=["id", *return_fields],
            ),
            arguments,
        )
        return {item["id"]: item for item in curs.fetchall()}
