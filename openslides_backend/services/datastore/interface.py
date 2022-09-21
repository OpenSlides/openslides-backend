from typing import (
    Any,
    ContextManager,
    Dict,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Union,
)

from datastore.shared.services.read_database import HistoryInformation
from datastore.shared.util import DeletedModelsBehaviour

from ...shared.filters import Filter
from ...shared.interfaces.collection_field_lock import CollectionFieldLock
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection, FullQualifiedId
from ...shared.typing import ModelMap
from .commands import GetManyRequest

PartialModel = Dict[str, Any]


LockResult = Union[bool, List[str]]


MappedFieldsPerFqid = Dict[FullQualifiedId, List[str]]


class BaseDatastoreService(Protocol):
    """
    Datastore defines the interface to the datastore.
    """

    # The key of this dictionary is a stringified FullQualifiedId or FullQualifiedField
    locked_fields: Dict[str, CollectionFieldLock]

    def get_database_context(self) -> ContextManager[None]:
        ...

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str],
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
    ) -> PartialModel:
        ...

    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        ...

    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Dict[int, PartialModel]:
        ...

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Dict[int, PartialModel]:
        ...

    def exists(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> bool:
        ...

    def count(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> int:
        ...

    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Optional[int]:
        ...

    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Optional[int]:
        ...

    def history_information(
        self, fqids: List[str]
    ) -> Dict[str, List[HistoryInformation]]:
        ...

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        ...

    def reserve_id(self, collection: Collection) -> int:
        ...

    def write(self, write_requests: Union[List[WriteRequest], WriteRequest]) -> None:
        ...

    def truncate_db(self) -> None:
        ...

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        ...

    def reset(self, hard: bool = True) -> None:
        ...

    def get_everything(self) -> Dict[Collection, Dict[int, PartialModel]]:
        ...

    def delete_history_information(self) -> None:
        ...


class DatastoreService(BaseDatastoreService):
    changed_models: ModelMap

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: Optional[List[str]] = None,
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
        use_changed_models: bool = True,
        raise_exception: bool = True,
    ) -> PartialModel:
        ...

    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        ...

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str] = [],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Dict[int, PartialModel]:
        ...

    def exists(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> bool:
        ...

    def count(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int:
        ...

    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Optional[int]:
        ...

    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Optional[int]:
        ...

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        """
        Returns whether the given model was deleted during this request or not.
        """

    def apply_changed_model(
        self, fqid: FullQualifiedId, instance: PartialModel, replace: bool = False
    ) -> None:
        ...


class Engine(Protocol):
    """
    Engine defines the interface to the engine used by the datastore.
    """

    def retrieve(
        self, endpoint: str, data: Optional[str]
    ) -> Tuple[Union[bytes, str], int]:
        ...
