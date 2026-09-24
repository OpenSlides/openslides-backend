from dataclasses import dataclass
from typing import Any, NewType, Union

from openslides_backend.shared.filters import Filter

_Table = NewType("_Table", str)
_View = NewType("_View", str)
_Column = NewType("_Column", str)

Table = Union[str, _Table]
View = Union[str, _View]
Column = Union[str, _Column]
Renames = tuple[dict[str, str], dict[str, dict[str, str]]]
ExtendedSqlArguments = list[str | int | list[str | int]]


@dataclass(frozen=True)
class ValuesSource:
    columns: list[Column]
    rows: list[dict[Column, Any]]
    join_on: list[Column]
    alias: str = "v"


@dataclass(frozen=True)
class JoinOn:
    right_column: Column
    left_column_def: tuple[Table | View, Column]

    @property
    def left_table(self) -> Table | View:
        return self.left_column_def[0]

    @property
    def left_column(self) -> Column:
        return self.left_column_def[1]


@dataclass(frozen=True)
class Join:
    table: Table | View
    join_on: list[JoinOn]
    filter: Filter | None = None

    def __post_init__(self) -> None:
        # TODO: move here validations from BaseMigration
        pass

    @property
    def collection(self) -> str:
        if self.table.endswith("_m") or self.table.endswith("_t"):
            return self.table[:-2]
        return self.table
