from typing import Any, Dict

from .patterns import FullQualifiedId

ModelMap = Dict[FullQualifiedId, Dict[str, Any]]

Schema = Dict[str, Any]


class DeletedModel(Dict):
    """ Used to mark deleted models which return None for each field """

    def __repr__(self) -> str:
        return "DeletedModel"
