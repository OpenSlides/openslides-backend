from typing import Any, Union

from .patterns import Collection, Id

PartialModel = dict[str, Any]
Model = dict[str, Any]
ModelMap = dict[Collection, dict[Id, PartialModel]]

Schema = dict[str, Any]

HistoryInformation = dict[str, list[str]]

JSON = Union[str, int, float, bool, None, dict[str, Any], list[Any]]

LockResult = Union[bool, list[str]]


class DeletedModel(dict):
    """Used to mark deleted models which return None for each field"""

    def __repr__(self) -> str:
        return "DeletedModel"
