from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

FilterData = Dict[str, Any]


class Filter(ABC):
    @abstractmethod
    def to_dict(self) -> FilterData:
        """Return a dict representation of this filter."""


class FilterOperator(Filter):
    def __init__(self, field: str, operator: str, value: Any) -> None:
        self.field = field
        self.operator = operator
        self.value = value

    def to_dict(self) -> FilterData:
        return {"field": self.field, "operator": self.operator, "value": self.value}


class And(Filter):
    def __init__(self, *filters: Filter) -> None:
        self.filters = filters

    def to_dict(self) -> FilterData:
        filters = list(map(lambda x: x.to_dict(), self.filters))
        return {"and_filter": filters}


class Or(Filter):
    def __init__(self, *filters: Filter) -> None:
        self.filters = filters

    def to_dict(self) -> FilterData:
        filters = list(map(lambda x: x.to_dict(), self.filters))
        return {"or_filter": filters}


class Not(Filter):
    def __init__(self, filter: Filter) -> None:
        self.filter = filter

    def to_dict(self) -> FilterData:
        return {"not_filter": self.filter.to_dict()}


def filter_visitor(filter: Filter, callback: Callable[[FilterOperator], None]) -> None:
    """
    Iterates over all nested filters of the given filter and executes the callback on
    each one FilterOperator that is found.
    """
    if isinstance(filter, FilterOperator):
        callback(filter)
    elif isinstance(filter, Not):
        filter_visitor(filter.filter, callback)
    elif isinstance(filter, (And, Or)):
        for f in filter.filters:
            filter_visitor(f, callback)
