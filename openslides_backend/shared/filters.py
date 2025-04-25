import typing
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias, Union

from openslides_backend.datastore.shared.util.self_validating_dataclass import (
    SelfValidatingDataclass,
)
from openslides_backend.shared.patterns import Field

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
                "enum": ["=", "!=", "<", ">", ">=", "<=", "~=", "%="],
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
FilterLiteral = Literal["=", "!=", "<", ">", ">=", "<=", "~=", "%="]

# Whoof, that's an ugly workaround... A bit of background:
# - The `dacite` package cannot handle `collections.abc.Sequence` (the replacement for the
#   deprecated `typing.Sequence`) correctly in python 3.10, therefore we need to use
#   `typing.Sequence` here. (With python 3.11, this bug seems to be fixed.)
# - On the other hand, `pyupgrade` automatically replaces `typing.Sequence` with
#   `collections.abc.Sequence` and provides no way to exclude single lines. Therefore, we have to
#   use this hack to be able to use `typing.Sequence` here.
Sequence: TypeAlias = getattr(typing, "Sequence")  # type: ignore


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
class FilterOperator(_FilterBase, SelfValidatingDataclass):
    field: Field
    operator: FilterLiteral
    value: Any

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
