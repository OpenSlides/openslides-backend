from abc import abstractmethod
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

    @abstractmethod
    def get_database_context(self) -> ContextManager[None]: ...

    @abstractmethod
    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str],
        position: Optional[int] = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
    ) -> PartialModel: ...

    @abstractmethod
    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        position: Optional[int] = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Dict[Collection, Dict[int, PartialModel]]: ...

    @abstractmethod
    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Dict[int, PartialModel]: ...

    @abstractmethod
    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Dict[int, PartialModel]: ...

    @abstractmethod
    def exists(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> bool: ...

    @abstractmethod
    def count(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> int: ...

    @abstractmethod
    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Optional[int]: ...

    @abstractmethod
    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> Optional[int]: ...

    @abstractmethod
    def history_information(
        self, fqids: List[str]
    ) -> Dict[str, List[HistoryInformation]]: ...

    @abstractmethod
    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]: ...

    @abstractmethod
    def reserve_id(self, collection: Collection) -> int: ...

    @abstractmethod
    def write(
        self, write_requests: Union[List[WriteRequest], WriteRequest]
    ) -> None: ...

    @abstractmethod
    def write_without_events(self, write_request: WriteRequest) -> None: ...

    @abstractmethod
    def truncate_db(self) -> None: ...

    @abstractmethod
    def is_deleted(self, fqid: FullQualifiedId) -> bool: ...

    @abstractmethod
    def reset(self, hard: bool = True) -> None: ...

    @abstractmethod
    def get_everything(self) -> Dict[Collection, Dict[int, PartialModel]]: ...

    @abstractmethod
    def delete_history_information(self) -> None: ...


class DatastoreService(BaseDatastoreService):
    changed_models: ModelMap

    @abstractmethod
    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str],
        position: Optional[int] = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
        use_changed_models: bool = True,
        raise_exception: bool = True,
    ) -> PartialModel: ...

    @abstractmethod
    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        position: Optional[int] = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Dict[Collection, Dict[int, PartialModel]]: ...

    @abstractmethod
    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Dict[int, PartialModel]: ...

    @abstractmethod
    def exists(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> bool: ...

    @abstractmethod
    def count(
        self,
        collection: Collection,
        filter: Filter,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int: ...

    @abstractmethod
    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Optional[int]: ...

    @abstractmethod
    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> Optional[int]: ...

    @abstractmethod
    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        """
        Returns whether the given model was deleted during this request or not.
        """

    @abstractmethod
    def apply_changed_model(
        self, fqid: FullQualifiedId, instance: PartialModel, replace: bool = False
    ) -> None: ...


class Engine(Protocol):
    """
    Engine defines the interface to the engine used by the datastore.
    """

    @abstractmethod
    def retrieve(
        self, endpoint: str, data: Optional[str]
    ) -> Tuple[Union[bytes, str], int]: ...
