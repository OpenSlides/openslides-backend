from typing import Any

from .patterns import FullQualifiedId

ModelMap = dict[FullQualifiedId, dict[str, Any]]

Schema = dict[str, Any]

HistoryInformation = dict[str, list[str]]


class DeletedModel(dict):
    """Used to mark deleted models which return None for each field"""

    def __repr__(self) -> str:
        return "DeletedModel"
