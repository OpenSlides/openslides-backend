from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Union

from psycopg import sql

from openslides_backend.shared.exceptions import BadCodingException, InvalidFormat
from openslides_backend.shared.patterns import FIELD_PATTERN, Field

filter_definitions_schema = {
    "filter": {
        "anyOf": [
            {"$ref": "#/$defs/filter_operator"},
            {"$ref": "#/$defs/not_filter"},
            {"$ref": "#/$defs/and_filter"},
            {"$ref": "#/$defs/or_filter"},
        ],
    },
    "filter_operator": {
        "type": "object",
        "properties": {
            "field": {"type": "string"},
            "value": {},
            "operator": {
                "type": "string",
                "enum": ["=", "!=", "<", ">", ">=", "<=", "~=", "%=", "in", "has"],
            },
        },
        "required": ["field", "value", "operator"],
    },
    "not_filter": {
        "type": "object",
        "properties": {"not_filter": {"$ref": "#/$defs/filter"}},
        "required": ["not_filter"],
    },
    "and_filter": {
        "type": "object",
        "properties": {
            "and_filter": {
                "type": "array",
                "items": {"$ref": "#/$defs/filter"},
            },
        },
        "required": ["and_filter"],
    },
    "or_filter": {
        "type": "object",
        "properties": {
            "or_filter": {
                "type": "array",
                "items": {"$ref": "#/$defs/filter"},
            },
        },
        "required": ["or_filter"],
    },
}


FilterData = dict[str, Any]
FilterLiteral = Literal["=", "!=", "<", ">", ">=", "<=", "~=", "%=", "in", "has"]
SqlArguments = list[str | int]


class _FilterBase(ABC):
    @abstractmethod
    def to_dict(self) -> FilterData:
        """Return a dict representation of this filter."""


class _ListFilterBase(_FilterBase, ABC):
    def __init__(
        self,
        arg: Union["Filter", Iterable["Filter"]] = [],
        *more_filters: "Filter",
        **kwargs: Iterable["Filter"],
    ) -> None:
        self._set_filters(
            (list(arg) if isinstance(arg, Iterable) else [arg])
            + list(more_filters)
            + list(kwargs.get(self._get_field_name(), []))
        )

    def to_dict(self) -> FilterData:
        filters = list(map(lambda x: x.to_dict(), self._get_filters()))
        return {self._get_field_name(): filters}

    def _get_filters(self) -> Sequence["Filter"]:
        return getattr(self, self._get_field_name())

    def _set_filters(self, filters: Sequence["Filter"]) -> None:
        setattr(self, self._get_field_name(), filters)

    def _get_field_name(self) -> str:
        return f"{type(self).__name__.lower()}_filter"

    def __hash__(self) -> int:
        return hash((self._get_field_name(),) + tuple(self._get_filters()))


@dataclass
class FilterOperator(_FilterBase):
    field: Field
    operator: FilterLiteral
    value: Any

    def __post_init__(self) -> None:
        if (
            self.field
            and isinstance(self.field, str)
            and not FIELD_PATTERN.match(self.field)
        ):
            raise Exception(
                f"Filter field {self.field} does not comply with field format."
            )

    def to_dict(self) -> FilterData:
        return {"field": self.field, "operator": self.operator, "value": self.value}

    def __hash__(self) -> int:
        return hash((self.field, self.operator, self.value))


# We need to explicitly repeat the __hash__ method in the And and Or filter since the dataclass
# wrapper will set them to None otherwise (see dataclass docs). This could be prevented by setting
# frozen=True on all dataclasses, but this leads to the custom constructor in _ListFilterBase no
# longer working.


@dataclass(init=False)
class And(_ListFilterBase):
    and_filter: Sequence["Filter"]

    def __hash__(self) -> int:
        return super().__hash__()


@dataclass(init=False)
class Or(_ListFilterBase):
    or_filter: Sequence["Filter"]

    def __hash__(self) -> int:
        return super().__hash__()


@dataclass
class Not(_FilterBase):
    not_filter: "Filter"

    def to_dict(self) -> FilterData:
        return {"not_filter": self.not_filter.to_dict()}

    def __hash__(self) -> int:
        return hash(("not_filter", self.not_filter))


Filter = Union[And, Or, Not, FilterOperator]


def filter_visitor(filter: Filter, callback: Callable[[FilterOperator], None]) -> None:
    """
    Iterates over all nested filters of the given filter and executes the callback on
    each one FilterOperator that is found.
    """
    if isinstance(filter, FilterOperator):
        callback(filter)
    elif isinstance(filter, Not):
        filter_visitor(filter.not_filter, callback)
    elif isinstance(filter, And):
        for f in filter.and_filter:
            filter_visitor(f, callback)
    elif isinstance(filter, Or):
        for f in filter.or_filter:
            filter_visitor(f, callback)


class BaseSqlQueryHelper:
    @classmethod
    def build_filter_str(
        cls,
        filter_: Filter,
        arguments: SqlArguments,
        collection: str,
        table_alias: str = "",
    ) -> sql.Composed | sql.Identifier:
        """
        appends the values to the arguments list
        returns the filter string
        """
        if isinstance(filter_, Not):
            return sql.SQL("NOT ({filter_str})").format(
                filter_str=cls.build_filter_str(
                    filter_.not_filter, arguments, collection, table_alias
                )
            )
        elif isinstance(filter_, Or):
            return sql.SQL(" OR ").join(
                sql.SQL("({filter_str})").format(
                    filter_str=cls.build_filter_str(
                        part, arguments, collection, table_alias
                    )
                )
                for part in filter_.or_filter
            )
        elif isinstance(filter_, And):
            return sql.SQL(" AND ").join(
                sql.SQL("({filter_str})").format(
                    filter_str=cls.build_filter_str(
                        part, arguments, collection, table_alias
                    )
                )
                for part in filter_.and_filter
            )
        elif isinstance(filter_, FilterOperator):
            if table_alias:
                table_column: sql.Composed | sql.Identifier = sql.SQL(
                    "{table_alias}.{column_name}"
                ).format(
                    table_alias=sql.Identifier(table_alias),
                    column_name=sql.Identifier(filter_.field),
                )
            else:
                table_column = sql.Identifier(filter_.field)
            if filter_.value is None:
                if filter_.operator not in ("=", "!="):
                    raise InvalidFormat("You can only compare to None with = or !=")
                operator = (
                    filter_.operator[::-1].replace("=", "IS").replace("!", " NOT")
                )
                condition = sql.SQL("{table_column} {operator} NULL").format(
                    table_column=table_column, operator=sql.SQL(operator)
                )
            else:
                if filter_.operator == "~=":
                    condition = sql.SQL(
                        "LOWER({table_column}) = LOWER(%s::text)"
                    ).format(table_column=table_column)
                elif filter_.operator == "%=":
                    condition = sql.SQL("{table_column} ILIKE %s::text").format(
                        table_column=table_column
                    )
                elif filter_.operator == "in":
                    condition = sql.SQL("{table_column} = ANY(%s)").format(
                        table_column=table_column
                    )
                elif filter_.operator == "has":
                    condition = sql.SQL("%s = ANY({table_column})").format(
                        table_column=table_column
                    )
                # TODO delete or use if all backend tests were run.
                # elif filter_.operator in ("=", "!=") and isinstance(filter_.value, str):
                #     condition = sql.SQL("{table_column} {filter_operator} %s::text").format(
                #         table_column=table_column, filter_operator=sql.SQL(filter_.operator)
                #     )
                elif filter_.operator in ("=", "!=") and isinstance(
                    filter_.value, list
                ):
                    condition = sql.SQL(
                        "{table_column} {filter_operator} %s{type}"
                    ).format(
                        table_column=table_column,
                        filter_operator=sql.SQL(filter_.operator),
                        type=cls.get_array_type(
                            (type(next(iter(filter_.value))) if filter_.value else int),
                            collection,
                            filter_.field,
                        ),
                    )
                else:
                    condition = sql.SQL("{table_column} {filter_operator} %s").format(
                        table_column=table_column,
                        filter_operator=sql.SQL(filter_.operator),
                    )
                arguments += [filter_.value]
            return condition
        else:
            raise BadCodingException("Invalid filter type")

    @staticmethod
    def get_enum_array_name(
        collection: str, field_name: str, *args: Any, **kwargs: Any
    ) -> str | None:
        raise NotImplementedError()

    @classmethod
    def get_array_type(
        cls, list_type: type, collection: str, field: str
    ) -> sql.Composable:
        if list_type == int:
            return sql.SQL("::integer[]")
        elif enum_array_name := cls.get_enum_array_name(collection, field):
            return sql.SQL(f"::{enum_array_name}")
        elif list_type == str:
            return sql.SQL("::text[]")
        raise ValueError("Only integer, string or enum lists are supported.")
