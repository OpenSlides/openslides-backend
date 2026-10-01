from collections import Counter
from dataclasses import dataclass
from typing import Any, NewType, Union

from psycopg import sql

from meta.dev.src.helper_get_names import HelperGetNames
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.filters import Filter
from openslides_backend.shared.patterns import Collection

_Table = NewType("_Table", str)
_View = NewType("_View", str)
_Column = NewType("_Column", str)

Table = Union[str, _Table]
View = Union[str, _View]
Column = Union[str, _Column]
Renames = tuple[dict[str, str], dict[str, dict[str, str]]]
ExtendedSqlArguments = list[str | int | list[str | int]]


@dataclass(frozen=True)
class TableRef:
    """
    A reference to a table or view.

    'migration' and 'is_view' define how value of table_name property is built from 'collection':
        is_view = False (default):
            migration = False -> collection_t
            migration = True -> collection_m
        is_view = True -> collection
    """

    collection: Collection
    migration: bool | None = None
    is_view: bool = False

    def __post_init__(self) -> None:
        table_type_settings = [self.is_view, self.migration is not None]
        if all(table_type_settings):
            raise BadCodingException(
                "'migration' parameter can only be applied when 'is_view = False'."
            )
        elif not any(table_type_settings):
            raise BadCodingException(
                "One out of 'is_view' and 'migration' must be defined."
            )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TableRef):
            return self.table_name == other.table_name
        if isinstance(other, str):
            return self.table_name == other
        raise BadCodingException(f"Can not compare TableRef object and {type(other)}.")

    def __hash__(self) -> int:
        return hash(self.table_name)

    @property
    def table_name(self) -> str:
        return (
            self.collection
            if self.is_view
            else HelperGetNames.get_table_name(self.collection, self.migration)
        )


@dataclass(frozen=True)
class JoinOn:
    """
    Describes a column mapping between a joined table and its left table:
        right_column - column in the joined table
        left_column - matching column in the left table
        left_table - definition of a table that serves as a join target
    """

    right_column: Column
    left_table: TableRef
    left_column: Column


@dataclass(frozen=True)
class Join:
    """
    Describes how a table should be joined to other tables:
        right_table - definition of a joined table
        join_on - columns mappings between the joined table and related left table(s)
        filter_right_table - optional filter applied to the joined table
    """

    right_table: TableRef
    join_on: list[JoinOn]
    filter_right_table: Filter | None = None


@dataclass(frozen=True)
class ColumnDataSource:
    """
    Describes how the table/view column is used as the data source.

    One of the options can be defined:
        * source_column - name of the column of the source table/view whose value
          should be copied directly into target_column.
        * transformed_column_value - an sql-expression that describes how
          target value should be computed from the data from one or multiple columns
          of the source table.
    """

    target_column: Column
    source_column: Column | None = None
    transformed_column_value: sql.Composed | None = None

    def __post_init__(self) -> None:
        value_settings = [
            self.source_column is not None,
            self.transformed_column_value is not None,
        ]

        if all(value_settings):
            raise BadCodingException(
                "Only one out of 'source_column' and 'transformed_column_value' can be defined."
            )
        elif not any(value_settings):
            raise BadCodingException(
                "One out of 'source_column' and 'transformed_column_value' must be defined."
            )

    def value(
        self, source_table: TableRef | None = None
    ) -> sql.Identifier | sql.Composed:
        if self.source_column is not None:
            if source_table is None:
                raise BadCodingException(
                    "'source_table' is required when 'source_column' is defined."
                )
            return sql.Identifier(source_table.table_name, self.source_column)
        assert self.transformed_column_value is not None
        return self.transformed_column_value


@dataclass(frozen=True)
class TableDataSource:
    """
    Describes how data from a joined table is mapped to target columns:
        * source_table - defines the source and how it is joined
        * source_data - maps the target columns to their corresponding source values
    """

    source_table: Join
    value_definition: list[ColumnDataSource]

    def __post_init__(self) -> None:
        if not self.value_definition:
            raise BadCodingException("'source_data' can not be empty.")

        target_columns = [data.target_column for data in self.value_definition]
        if duplicates := [
            column for column, count in Counter(target_columns).items() if count > 1
        ]:
            raise BadCodingException(
                f"'source_data' defines multiple sources for column(s): {duplicates}."
            )

    @property
    def values_map(self) -> dict[Column, sql.Identifier | sql.Composed]:
        return {
            data.target_column: data.value(self.source_table.right_table)
            for data in self.value_definition
        }


@dataclass(frozen=True)
class _CopyFromTables:
    """
    Base dataclass describing how target values should be built
    from the data from other tables and views.
    """

    copy_data: list[TableDataSource]

    def _extra_checks(self) -> list[str]:
        """
        Re-define in the child class to add checks specific for the dataclass.
        """
        return []

    @property
    def root_source(self) -> TableRef:
        """
        Re-define in the child dataclass to define the table that should
        serve as the root of the JOIN-statements.
        """
        raise NotImplementedError()

    @property
    def joined_sources(self) -> list[TableDataSource]:
        """
        Re-define in the child dataclass to define the tables that should
        be joined to the root_source.
        """
        raise NotImplementedError()

    @property
    def target_columns(self) -> list[Column]:
        return [
            target_data.target_column
            for data_source in self.copy_data
            for target_data in data_source.value_definition
        ]

    @property
    def select_columns(self) -> list[sql.Identifier | sql.Composed]:
        return [
            target_data.value(data_source.source_table.right_table)
            for data_source in self.copy_data
            for target_data in data_source.value_definition
        ]

    @property
    def copy_data_map(self) -> dict[Column, sql.Composable]:
        """
        Maps target columns to the corresponding sql-parts that describe the values to be set.
        """
        return {
            data.target_column: data.value(data_source.source_table.right_table)
            for data_source in self.copy_data
            for data in data_source.value_definition
        }

    def __post_init__(self) -> None:
        errors = []
        if not self.copy_data:
            errors.append("'copy_data' can not be empty.")
        if extra_errors := self._extra_checks():
            errors.extend(extra_errors)
        if errors:
            raise BadCodingException("\n".join(errors))

        # Check one source per target column
        if duplicates := [
            column
            for column, count in Counter(self.target_columns).items()
            if count > 1
        ]:
            errors.append(
                f"'copy_data' defines multiple sources for column(s): {duplicates}."
            )

        # Check join tree
        root_table = next(iter(self.copy_data)).source_table
        if [
            left_table
            for join_on_data in root_table.join_on
            if (left_table := join_on_data.left_table) != self.root_source
        ]:
            if hasattr(self, "target_table"):
                errors.append(
                    "Root table from copy_data must join to the target_table."
                )
            else:
                errors.append(
                    "Root table from copy_data must join to the main_source_table."
                )
        else:
            seen_sources = {self.root_source}
            for source_table in self.copy_data[1:]:
                right_table = source_table.source_table.right_table
                for join_on_data in source_table.source_table.join_on:
                    if right_table == (left_table := join_on_data.left_table):
                        errors.append(
                            f"Can not join {right_table.table_name} to itself."
                        )
                    elif left_table not in seen_sources:
                        errors.append(
                            f"Can not join {right_table.table_name} to {left_table.table_name} "
                            f"because {left_table.table_name} has to be joined first."
                        )
                seen_sources.add(right_table)

        if errors:
            raise BadCodingException("\n".join(errors))


@dataclass(frozen=True)
class UpdateFromTables(_CopyFromTables):
    """
    Describes one or more joined tables as data sources for UPDATE operations.

    'copy_data' must not be empty.
    Each target column in 'copy_data' must have a single source.
    Source tables must form a valid join tree rooted at 'target_table'.
    """

    target_table: TableRef

    def _extra_checks(self) -> list[str]:
        if empty_join_on := [
            i
            for i in range(len(self.copy_data))
            if not self.copy_data[i].source_table.join_on
        ]:
            return [
                f"Items {empty_join_on} of 'copy_data' contain 'source_table's with empty 'join_on'."
            ]
        return []

    @property
    def root_source(self) -> TableRef:
        return self.target_table

    @property
    def joined_sources(self) -> list[TableDataSource]:
        return self.copy_data


@dataclass(frozen=True)
class InsertFromTables(_CopyFromTables):
    """
    Describes one or more joined tables as data sources for INSERT operations.

    'copy_data' must not be empty.
    Each target column in 'copy_data' must have a single source.
    Source tables must form a valid join tree rooted at 'main_source_table'
    or the first source table.
    """

    main_source_table: TableRef | None = None
    filter_main_source_table: Filter | None = None

    def _extra_checks(self) -> list[str]:
        errors = []
        if len(self.copy_data) > 1:
            if self.main_source_table is None:
                errors.append(
                    "'main_source_table' is required when more than one "
                    "source table is defined."
                )
            if empty_join_on := [
                i
                for i in range(len(self.copy_data[1:]))
                if not self.copy_data[i].source_table.join_on
            ]:
                return [
                    f"Items {empty_join_on} of 'copy_data' contain 'source_table's with empty 'join_on'."
                ]
        elif not self.main_source_table and (
            join_on := self.copy_data[0].source_table.join_on
        ):
            errors.append(
                f"'join_on = {join_on}' is redundant in the 'Join' object because only 1 data source "
                "is defined. Skip this value by setting 'join_on = []'."
            )
        return errors

    @property
    def root_source(self) -> TableRef:
        if self.main_source_table is not None:
            return self.main_source_table
        return self.copy_data[0].source_table.right_table

    @property
    def joined_sources(self) -> list[TableDataSource]:
        if self.main_source_table is None:
            return self.copy_data[1:]
        return self.copy_data


@dataclass(frozen=True)
class ArrayDiff:
    """
    Describes changes to an array field.

    At least one operation (add/remove/replace) must be provided.
    All values must have the same type.
    Operations must not contain overlapping or identical values.
    """

    add: set[Any] | None = None
    remove: set[Any] | None = None
    replace: dict[Any, Any] | None = None

    def __post_init__(self) -> None:
        if not self.add and not self.remove and not self.replace:
            raise BadCodingException(
                "At least one of 'add', 'remove' or 'replace' must be provided."
            )
        replace_dict = self.replace or {}
        if (
            len(
                {
                    type(item)
                    for item in [
                        *(self.add or []),
                        *(self.remove or []),
                        *replace_dict.keys(),
                        *replace_dict.values(),
                    ]
                }
            )
            > 1
        ):
            raise BadCodingException(
                "All values in 'add', 'remove' and 'replace' must have the same type."
            )

        errors: list[str] = []
        overlaps: list[tuple[str, str, set[Any]]] = []

        if self.add and self.remove and (overlap := self.add & self.remove):
            overlaps.append(("add", "remove", overlap))
        if self.replace:
            replace_keys = set(self.replace.keys())
            replace_values = set(self.replace.values())
            for parameter, values in [("add", self.add), ("remove", self.remove)]:
                if values and (overlap := values & replace_keys):
                    overlaps.append((parameter, "replace keys", overlap))
            if overlap := replace_keys & replace_values:
                overlaps.append(("replace keys", "replace values", overlap))
            for old, new in self.replace.items():
                if old == new:
                    errors.append(f"Replacement value cannot be identical: {old}")

        for parameter1, parameter2, values in overlaps:
            errors.append(
                f"'{parameter1}' and '{parameter2}' contain should not have the same values "
                f"within one update_array call. Overlapping values: {sorted(list(values))}."
            )
        if errors:
            raise BadCodingException("\n".join(errors))


@dataclass(frozen=True)
class ValuesSource:
    """
    Describes the values used as the source of a mass update.

    'rows' contains dictionaries whose keys identify the columns in the
    generated VALUES table. Each dictionary must contain the same non-empty
    set of columns.

    All columns in 'rows' must exist in the target table.
    2 types of columns have to be present in the dictionaries:
        * columns from 'join_on_columns' - to match source rows with rows
          in the target table
        * columns with tartget values to be written to the target table.
    """

    rows: list[dict[Column, Any]]
    join_on_columns: list[Column]
    alias: str = "v"

    def __post_init__(self) -> None:
        errors = []
        if not self.rows:
            errors.append("'rows' must not be empty.")
        elif [row for row in self.rows if not row]:
            errors.append("'rows' must not contain empty dicts.")
        if not self.join_on_columns:
            errors.append("'join_on_columns' must not be empty.")
        if errors:
            raise BadCodingException("\n".join(errors))

        values_columns_set = set(self.values_columns)
        join_on_columns_set = set(self.join_on_columns)
        if len(self.join_on_columns) != len(join_on_columns_set):
            errors.append("'join_on_columns' must not contain duplicates.")

        if values_columns_set == join_on_columns_set:
            errors.append(
                "Dictionaries from 'rows' must contain columns "
                "other than 'join_on_columns'."
            )
        elif not join_on_columns_set.issubset(values_columns_set):
            errors.append(
                "Dictionaries from 'rows' must include all the "
                "columns names from 'join_on_columns'."
            )

        if not all(set(row) == values_columns_set for row in self.rows[1:]):
            errors.append("All dictionaries in 'values_map' must have the same keys.")

        if errors:
            raise BadCodingException("\n".join(errors))

    @property
    def values_columns(self) -> list[Column]:
        return list(self.rows[0].keys())

    @property
    def target_columns(self) -> list[Column]:
        return [
            column
            for column in self.values_columns
            if column not in self.join_on_columns
        ]

    @property
    def select_columns(self) -> list[sql.Identifier]:
        return [sql.Identifier(self.alias, column) for column in self.target_columns]
