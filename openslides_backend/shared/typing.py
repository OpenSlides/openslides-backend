from typing import Any, TypedDict, Union

from .patterns import Collection, FullQualifiedId, Id

PartialModel = dict[str, Any]
Model = dict[str, Any]
ModelMap = dict[Collection, dict[Id, PartialModel]]

Schema = dict[str, Any]


class HistoryInformationData(TypedDict):
    entries: list[str]


HistoryInformation = dict[FullQualifiedId, HistoryInformationData]

JSON = Union[str, int, float, bool, None, dict[str, Any], list[Any]]

LockResult = Union[bool, list[str]]


class DeletedModel(dict):
    """Used to mark deleted models which return None for each field"""

    def __repr__(self) -> str:
        return "DeletedModel"
