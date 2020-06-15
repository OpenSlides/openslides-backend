from enum import Enum
from typing import Any, Dict, List, Sequence

from mypy_extensions import TypedDict
from typing_extensions import Protocol

from ...shared.filters import Filter
from ...shared.patterns import Collection, FullQualifiedId
from .commands import Command, GetManyRequest

PartialModel = Dict[str, Any]
Found = TypedDict("Found", {"exists": bool, "position": int})
Count = TypedDict("Count", {"count": int, "position": int})
Aggregate = Dict[str, Any]  # TODO: This interface seams to be wrong.


class DeletedModelsBehaviour(Enum):
    NO_DELETED = 1
    ONLY_DELETED = 2
    ALL_MODELS = 3


class Datastore(Protocol):
    """
    Datastore defines the interface to the datastore.
    """

    # The key of this dictionary is a stringified FullQualifiedId or FullQualifiedField
    locked_fields: Dict[str, int]

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> PartialModel:
        ...

    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        ...

    def get_all(
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

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        ...

    def reserve_id(self, collection: Collection) -> int:
        ...


# TODO: Use proper typing here.
EngineResponse = Any


class Engine(Protocol):
    """
    Engine defines the interface to the engine used by the datastore. This will
    be the HTTPEngine per default
    """

    def get(self, data: Command) -> EngineResponse:
        ...

    def get_many(self, data: Command) -> EngineResponse:
        ...

    def get_all(self, data: Command) -> EngineResponse:
        ...

    def filter(self, data: Command) -> EngineResponse:
        ...

    def exists(self, data: Command) -> EngineResponse:
        ...

    def count(self, data: Command) -> EngineResponse:
        ...

    def min(self, data: Command) -> EngineResponse:
        ...

    def max(self, data: Command) -> EngineResponse:
        ...
