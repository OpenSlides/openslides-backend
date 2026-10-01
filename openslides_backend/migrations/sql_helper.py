from typing import Any

from psycopg import Cursor, sql
from psycopg.rows import DictRow

from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.migrations.patterns import (
    Column,
    ExtendedSqlArguments,
    Join,
    JoinOn,
    Table,
    ValuesSource,
    View,
)
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.filters import BaseSqlQueryHelper, SqlArguments
from openslides_backend.shared.patterns import Collection, Field


class MigrationSqlHelper(BaseSqlQueryHelper):
    # -- Override not implemented parent method --
    @staticmethod
    def get_array_type(
        collection: Collection, field: Field, curs: Cursor[DictRow]
    ) -> sql.Composable:
        table_name = HelperGetNames.get_table_name(collection)
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
                    table_name=table_name,
                    column_name=field,
                )
            ).fetchone()
            or {}
        )
        if element_type_name := result.get("element_type_name"):
            return sql.SQL(f"::{element_type_name}[]")
        raise BadCodingException(f"{table_name}/{field} is not an array column.")

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
        else:
            return sql.SQL("({column_names}) = ({placeholders})").format(
                column_names=MigrationSqlHelper.join_columns(columns),
                placeholders=MigrationSqlHelper.get_joined_placeholders(values),
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
    def get_value_assignment(
        target_column: Column,
        value: sql.Composable,
        target_table: str | None = None,
    ) -> sql.Composed:
        return sql.SQL("{target} = {value}").format(
            target=MigrationSqlHelper._build_identifier(target_table, target_column),
            value=value,
        )

    @staticmethod
    def get_column_assignment(
        target_column: Column,
        target_table: str | None = None,
        source_column: Column | None = None,
        source_table: str | None = None,
    ) -> sql.Composed:
        if source_column is None:
            source_column = target_column
        return sql.SQL("{target} = {source}").format(
            target=MigrationSqlHelper._build_identifier(target_table, target_column),
            source=MigrationSqlHelper._build_identifier(source_table, source_column),
        )

    # -- Methods for building parts for ARRAYs updates --
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
        join: Join, filter_string: sql.Composable
    ) -> sql.Composed:
        return sql.SQL("EXISTS (SELECT 1 FROM {joined_table} WHERE {where})").format(
            joined_table=sql.Identifier(join.right_table.table_name),
            where=MigrationSqlHelper.join_conditions(
                [
                    *MigrationSqlHelper.get_conditions_for_join(
                        join.right_table.table_name, join.join_on
                    ),
                    filter_string,
                ]
            ),
        )

    @staticmethod
    def get_conditions_for_join(
        right_table: str, join_on_columns: list[JoinOn]
    ) -> list[sql.Composable]:
        return [
            sql.SQL("{left_table}.{left_column} = {right_table}.{right_column}").format(
                right_table=sql.Identifier(right_table),
                right_column=sql.Identifier(join_on.right_column),
                left_table=sql.Identifier(join_on.left_table.table_name),
                left_column=sql.Identifier(join_on.left_column),
            )
            for join_on in join_on_columns
        ]

    @staticmethod
    def join_conditions(conditions: list[sql.Composable]) -> sql.Composable:
        if not conditions:
            raise BadCodingException("Filter condition list must not be empty")

        return sql.SQL(" AND ").join(
            sql.SQL("({condition})").format(condition=condition)
            for condition in conditions
        )

    # -- Methods for building FROM part --
    @staticmethod
    def build_values_table(
        values_source: ValuesSource, arguments: SqlArguments
    ) -> sql.Composed:
        arguments.extend(
            row[column]
            for row in values_source.rows
            for column in values_source.values_columns
        )
        return sql.SQL("(VALUES {values}) AS {alias}({columns})").format(
            values=sql.SQL(", ").join(
                sql.SQL("({placeholders})").format(
                    placeholders=MigrationSqlHelper.get_joined_placeholders(
                        values_source.values_columns
                    )
                )
                for _ in values_source.rows
            ),
            alias=sql.Identifier(values_source.alias),
            columns=MigrationSqlHelper.join_columns(values_source.values_columns),
        )

    @staticmethod
    def join_columns(columns: list[Column]) -> sql.Composable:
        assert columns
        return sql.SQL(", ").join(sql.Identifier(column) for column in columns)

    @staticmethod
    def get_joined_placeholders(values: list[Any]) -> sql.Composable:
        assert values
        return sql.SQL(", ").join(sql.Placeholder() * len(values))

    @staticmethod
    def join_tables(
        tables: list[sql.Composable],
    ) -> sql.Composable:
        if not tables:
            return sql.SQL("")
        return sql.SQL(" ") + sql.SQL(" ").join(tables)

    # -- Methods for building the queries --
    @staticmethod
    def normalize_from(from_part: sql.Composable | None) -> sql.Composable:
        if from_part is None:
            return sql.SQL("")
        return sql.SQL(" FROM {from_part}").format(from_part=from_part)

    @staticmethod
    def join_table_parts(
        table_parts: list[tuple[str | sql.Composed, list[sql.Composable]]] | None,
    ) -> sql.Composable:
        if not table_parts:
            return sql.SQL("")
        return MigrationSqlHelper.join_tables(
            [
                sql.SQL("JOIN {right_table} ON {conditions}").format(
                    right_table=(
                        sql.Identifier(table[0])
                        if isinstance(table[0], str)
                        else table[0]
                    ),
                    conditions=sql.SQL(" AND ").join(
                        sql.SQL("({condition})").format(condition=condition)
                        for condition in table[1]
                    ),
                )
                for table in table_parts
            ]
        )

    @staticmethod
    def normalize_where(
        condition: sql.Composable | list[sql.Composable] | None,
    ) -> sql.Composable:
        if condition is None:
            return sql.SQL("")

        if isinstance(condition, list):
            condition = MigrationSqlHelper.join_conditions(condition)

        return sql.SQL(" WHERE {condition}").format(condition=condition)

    @staticmethod
    def build_update_entries_sql(
        collection_or_table_name: str,
        set_part: sql.Composable,
        source_table: sql.Composable | None = None,
        joined_tables: (
            list[tuple[str | sql.Composed, list[sql.Composable]]] | None
        ) = None,
        filter_condition: sql.Composable | list[sql.Composable] | None = None,
    ) -> sql.Composed:
        return sql.SQL(
            "UPDATE {target_table} "
            "SET {set_part}"
            "{from_part}"
            "{joined_tables}"
            "{where}"
        ).format(
            target_table=sql.Identifier(
                HelperGetNames.get_table_name(collection_or_table_name)
            ),
            set_part=set_part,
            from_part=MigrationSqlHelper.normalize_from(source_table),
            joined_tables=MigrationSqlHelper.join_table_parts(joined_tables),
            where=MigrationSqlHelper.normalize_where(filter_condition),
        )

    @staticmethod
    def build_insert_from_other_table_sql(
        source_table: Table | View,
        target_table: Table,
        target_columns: sql.Composable,
        select_columns: sql.Composed,
        joined_tables: list[tuple[str | sql.Composed, list[sql.Composable]]],
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
            "SELECT {select_columns} "
            "FROM {source_table}"
            "{joined_tables}"
            "{where}"
            "{returning}"
        ).format(
            target_table=sql.Identifier(target_table),
            target_columns=target_columns,
            select_columns=select_columns,
            source_table=sql.Identifier(source_table),
            joined_tables=MigrationSqlHelper.join_table_parts(joined_tables),
            where=MigrationSqlHelper.normalize_where(condition),
            returning=(
                sql.SQL(" RETURNING {return_fields}").format(
                    return_fields=MigrationSqlHelper.join_columns(return_fields)
                )
                if return_fields
                else sql.SQL("")
            ),
        )
