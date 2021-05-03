from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from shared.util import And as BaseAnd
from shared.util import FilterOperator as BaseFilterOperator
from shared.util import Not as BaseNot
from shared.util import Or as BaseOr

FilterData = Dict[str, Any]


class Filter(ABC):
    @abstractmethod
    def to_dict(self) -> FilterData:
        """Return a dict representation of this filter."""


class FilterOperator(Filter, BaseFilterOperator):
    def to_dict(self) -> FilterData:
        return {"field": self.field, "operator": self.operator, "value": self.value}


class And(Filter, BaseAnd):
    def __init__(self, *filters: Filter) -> None:
        super().__init__(filters)

    def to_dict(self) -> FilterData:
        filters = list(map(lambda x: x.to_dict(), self.and_filter))
        return {"and_filter": filters}


class Or(Filter, BaseOr):
    def __init__(self, *filters: Filter) -> None:
        super().__init__(filters)

    def to_dict(self) -> FilterData:
        filters = list(map(lambda x: x.to_dict(), self.or_filter))
        return {"or_filter": filters}


class Not(Filter, BaseNot):
    def to_dict(self) -> FilterData:
        return {"not_filter": self.not_filter.to_dict()}


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
