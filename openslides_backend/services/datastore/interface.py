from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from typing_extensions import Protocol

from ...shared.filters import Filter
from ...shared.interfaces.collection_field_lock import CollectionFieldLock
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection, FullQualifiedId
from ...shared.typing import ModelMap
from .commands import GetManyRequest
from .deleted_models_behaviour import (
    DeletedModelsBehaviour,
    InstanceAdditionalBehaviour,
)

PartialModel = Dict[str, Any]


class DatastoreService(Protocol):
    """
    Datastore defines the interface to the datastore.
    """

    # The key of this dictionary is a stringified FullQualifiedId or FullQualifiedField
    locked_fields: Dict[str, CollectionFieldLock]
    additional_relation_models: ModelMap

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = False,
    ) -> PartialModel:
        ...

    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = False,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        ...

    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str] = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = False,
    ) -> Dict[int, PartialModel]:
        ...

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str] = [],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = False,
    ) -> Dict[int, PartialModel]:
        ...

    def exists(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = False,
    ) -> bool:
        ...

    def count(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = False,
    ) -> int:
        ...

    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        type: str = "int",
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = False,
    ) -> Optional[int]:
        ...

    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        type: str = "int",
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = False,
    ) -> Optional[int]:
        ...

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        ...

    def reserve_id(self, collection: Collection) -> int:
        ...

    def write(self, write_requests: Union[List[WriteRequest], WriteRequest]) -> None:
        ...

    def truncate_db(self) -> None:
        ...

    def update_additional_models(
        self, fqid: FullQualifiedId, instance: Dict[str, Any], replace: bool = False
    ) -> None:
        ...

    def fetch_model(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str],
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = False,
        db_additional_relevance: InstanceAdditionalBehaviour = InstanceAdditionalBehaviour.ONLY_DBINST,
        exception: bool = True,
    ) -> Dict[str, Any]:
        ...

    def reset(self) -> None:
        ...


class Engine(Protocol):
    """
    Engine defines the interface to the engine used by the datastore. This will
    be the HTTPEngine per default
    """

    def retrieve(self, endpoint: str, data: str) -> Tuple[bytes, int]:
        ...
