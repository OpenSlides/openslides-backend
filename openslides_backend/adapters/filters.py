from typing import Any, List, Union

Filter = Union["And", "Or", "Not", "FilterOperator"]


class FilterOperator:
    def __init__(self, field: str, value: Any, operator: str) -> None:
        self.field = field
        self.value = value
        self.operator = operator


class And:
    def __init__(self, value: List[Filter]) -> None:
        self.value = value


class Or:
    def __init__(self, value: List[Filter]) -> None:
        self.value = value


class Not:
    def __init__(self, value: Filter) -> None:
        self.value = value
