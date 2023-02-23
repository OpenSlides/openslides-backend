from typing import Any, Dict, List

from .patterns import FullQualifiedId

ModelMap = Dict[FullQualifiedId, Dict[str, Any]]

Schema = Dict[str, Any]

HistoryInformation = Dict[str, List[str]]


class DeletedModel(Dict):
    """Used to mark deleted models which return None for each field"""

    def __repr__(self) -> str:
        return "DeletedModel"
