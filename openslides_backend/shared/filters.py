from abc import ABC, abstractmethod
from typing import Any, Dict, List

FilterData = Dict[str, Any]


class Filter(ABC):
    @abstractmethod
    def to_dict(self) -> FilterData:
        ...


class FilterOperator(Filter):
    def __init__(self, field: str, value: Any, operator: str) -> None:
        self.field = field
        self.value = value
        self.operator = operator

    def to_dict(self) -> FilterData:
        return {"field": self.field, "value": self.value, "operator": self.operator}


class And(Filter):
    def __init__(self, value: List[Filter]) -> None:
        self.value = value

    def to_dict(self) -> FilterData:
        filters = list(map(lambda x: x.to_dict(), self.value))
        return {"and_filter": filters}


class Or(Filter):
    def __init__(self, value: List[Filter]) -> None:
        self.value = value

    def to_dict(self) -> FilterData:
        filters = list(map(lambda x: x.to_dict(), self.value))
        return {"or_filter": filters}


class Not(Filter):
    def __init__(self, value: Filter) -> None:
        self.value = value

    def to_dict(self) -> FilterData:
        return {"not_filter": self.value.to_dict()}
