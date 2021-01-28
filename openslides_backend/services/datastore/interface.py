from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from mypy_extensions import TypedDict
from typing_extensions import Protocol

from ...shared.filters import Filter
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection, FullQualifiedId
from .commands import GetManyRequest
from .deleted_models_behaviour import DeletedModelsBehaviour

PartialModel = Dict[str, Any]
Found = TypedDict("Found", {"exists": bool})
Count = TypedDict("Count", {"count": int})
OptionalInt = Optional[int]


class DatastoreService(Protocol):
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
        get_deleted_models: DeletedModelsBehaviour = None,
        lock_result: bool = False,
    ) -> PartialModel:
        ...

    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = None,
        lock_result: bool = False,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        ...

    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str] = None,
        get_deleted_models: DeletedModelsBehaviour = None,
        lock_result: bool = False,
    ) -> Dict[int, PartialModel]:
        ...

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str] = [],
        get_deleted_models: DeletedModelsBehaviour = None,
        lock_result: bool = False,
    ) -> Dict[int, PartialModel]:
        ...

    def exists(
        self, collection: Collection, filter: Filter, lock_result: bool = False
    ) -> Found:
        ...

    def count(
        self, collection: Collection, filter: Filter, lock_result: bool = False
    ) -> Count:
        ...

    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        type: str = None,
        lock_result: bool = False,
    ) -> OptionalInt:
        ...

    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        type: str = None,
        lock_result: bool = False,
    ) -> OptionalInt:
        ...

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        ...

    def reserve_id(self, collection: Collection) -> int:
        ...

    def write(self, write_requests: Union[List[WriteRequest], WriteRequest]) -> None:
        ...

    def truncate_db(self) -> None:
        ...


class Engine(Protocol):
    """
    Engine defines the interface to the engine used by the datastore. This will
    be the HTTPEngine per default
    """

    def retrieve(self, endpoint: str, data: str) -> Tuple[bytes, int]:
        ...
