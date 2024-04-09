from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Sequence
from typing import Any, Union

from openslides_backend.datastore.shared.util import And as BaseAnd
from openslides_backend.datastore.shared.util import (
    FilterOperator as BaseFilterOperator,
)
from openslides_backend.datastore.shared.util import Not as BaseNot
from openslides_backend.datastore.shared.util import Or as BaseOr

FilterData = dict[str, Any]


class _FilterBase(ABC):
    @abstractmethod
    def to_dict(self) -> FilterData:
        """Return a dict representation of this filter."""


class _ListFilterBase(_FilterBase, ABC):
    def __init__(
        self, arg: Union["Filter", Iterable["Filter"]], *more_filters: "Filter"
    ) -> None:
        self._set_filters(
            (list(arg) if isinstance(arg, Iterable) else [arg]) + list(more_filters)
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


class FilterOperator(_FilterBase, BaseFilterOperator):
    def to_dict(self) -> FilterData:
        return {"field": self.field, "operator": self.operator, "value": self.value}

    def __hash__(self) -> int:
        return hash((self.field, self.operator, self.value))


class And(_ListFilterBase, BaseAnd):
    and_filter: Sequence["Filter"]


class Or(_ListFilterBase, BaseOr):
    or_filter: Sequence["Filter"]


class Not(_FilterBase, BaseNot):
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
