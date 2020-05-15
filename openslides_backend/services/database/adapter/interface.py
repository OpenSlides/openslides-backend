from enum import Enum
from typing import Any, Dict, List

from mypy_extensions import TypedDict
from typing_extensions import Protocol

from openslides_backend.shared.interfaces import Filter
from openslides_backend.shared.patterns import Collection, FullQualifiedId

PartialModel = Dict[str, Any]
Found = TypedDict("Found", {"exists": bool, "position": int})
Count = TypedDict("Count", {"count": int, "position": int})
Aggregate = Dict[str, Any]


class DeletedModelsBehaviour(Enum):
    NO_DELETED = 1
    ONLY_DELETED = 2
    ALL_MODELS = 3


class GetManyRequest:
    """Encapsulates a single GetManyRequests
    """

    def __init__(
        self, collection: Collection, ids: List[int], mapped_fields: List[str] = None,
    ):
        self.collection = collection
        self.ids = ids
        self.mapped_fields = mapped_fields

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        result["collection"] = str(self.collection)
        if self.ids is not None:
            result["ids"] = self.ids
        if self.mapped_fields is not None:
            result["mapped_fields"] = self.mapped_fields
        return result


class Datastore(Protocol):
    """Datastore defines the interface to the datastore
    """

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> PartialModel:
        ...

    def getMany(
        self,
        get_many_requests: List[GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> Dict[str, Dict[int, PartialModel]]:
        ...

    def getManyByFQIDs(
        self, ids: List[FullQualifiedId]
    ) -> Dict[str, Dict[int, PartialModel]]:
        ...

    def getAll(
        self,
        collection: Collection,
        mapped_fields: List[str] = None,
        get_deleted_models: int = None,
    ) -> List[PartialModel]:
        ...

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
    ) -> List[PartialModel]:
        ...

    def exists(self, collection: Collection, filter: Filter) -> Found:
        ...

    def count(self, collection: Collection, filter: Filter) -> Count:
        ...

    def min(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        ...

    def max(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        ...
