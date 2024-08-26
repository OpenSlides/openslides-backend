from abc import abstractmethod
from collections.abc import Sequence
from typing import Any, ContextManager, Protocol, Union

from openslides_backend.datastore.shared.services.read_database import (
    HistoryInformation,
)
from openslides_backend.datastore.shared.util import DeletedModelsBehaviour

from ...shared.filters import Filter
from ...shared.interfaces.collection_field_lock import CollectionFieldLock
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection, FullQualifiedId
from ...shared.typing import ModelMap
from .commands import GetManyRequest

PartialModel = dict[str, Any]


LockResult = Union[bool, list[str]]


MappedFieldsPerFqid = dict[FullQualifiedId, list[str]]


class BaseDatastoreService(Protocol):
    """
    Datastore defines the interface to the datastore.
    """

    # The key of this dictionary is a stringified FullQualifiedId or FullQualifiedField
    locked_fields: dict[str, CollectionFieldLock]

    @abstractmethod
    def get_database_context(self) -> ContextManager[None]: ...

    @abstractmethod
    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: list[str],
        position: int | None = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
    ) -> PartialModel: ...

    @abstractmethod
    def get_many(
        self,
        get_many_requests: list[GetManyRequest],
        position: int | None = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> dict[Collection, dict[int, PartialModel]]: ...

    @abstractmethod
    def get_all(
        self,
        collection: Collection,
        mapped_fields: list[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> dict[int, PartialModel]: ...

    @abstractmethod
    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: list[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> dict[int, PartialModel]: ...

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
    ) -> int | None: ...

    @abstractmethod
    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
    ) -> int | None: ...

    @abstractmethod
    def history_information(
        self, fqids: list[str]
    ) -> dict[str, list[HistoryInformation]]: ...

    @abstractmethod
    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]: ...

    @abstractmethod
    def reserve_id(self, collection: Collection) -> int: ...

    @abstractmethod
    def write(self, write_requests: list[WriteRequest] | WriteRequest) -> None: ...

    @abstractmethod
    def write_without_events(self, write_request: WriteRequest) -> None: ...

    @abstractmethod
    def is_deleted(self, fqid: FullQualifiedId) -> bool: ...

    @abstractmethod
    def reset(self, hard: bool = True) -> None: ...

    @abstractmethod
    def get_everything(self) -> dict[Collection, dict[int, PartialModel]]: ...

    @abstractmethod
    def delete_history_information(self) -> None: ...


class DatastoreService(BaseDatastoreService):
    changed_models: ModelMap

    @abstractmethod
    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: list[str],
        position: int | None = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
        use_changed_models: bool = True,
        raise_exception: bool = True,
    ) -> PartialModel: ...

    @abstractmethod
    def get_many(
        self,
        get_many_requests: list[GetManyRequest],
        position: int | None = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> dict[Collection, dict[int, PartialModel]]: ...

    @abstractmethod
    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: list[str],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> dict[int, PartialModel]: ...

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
    ) -> int | None: ...

    @abstractmethod
    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None: ...

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
    def retrieve(self, endpoint: str, data: str | None) -> tuple[bytes | str, int]: ...
