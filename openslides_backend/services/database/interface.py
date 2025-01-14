from abc import abstractmethod
from collections.abc import Sequence
from typing import Any, ContextManager, Protocol, Union

from ...shared.filters import Filter
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection, FullQualifiedId
from .commands import GetManyRequest

PartialModel = dict[str, Any]


LockResult = Union[bool, list[str]]


MappedFieldsPerFqid = dict[FullQualifiedId, list[str]]


class Database(Protocol):
    """
    Database defines the interface to the database.
    """

    @abstractmethod
    def get_database_context(self) -> ContextManager[None]: ...

    @abstractmethod
    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: list[str],
        position: int | None = None,
        lock_result: LockResult = True,
    ) -> PartialModel: ...

    @abstractmethod
    def get_many(
        self,
        get_many_requests: list[GetManyRequest],
        position: int | None = None,
        lock_result: LockResult = True,
    ) -> dict[Collection, dict[int, PartialModel]]: ...

    @abstractmethod
    def get_all(
        self,
        collection: Collection,
        mapped_fields: list[str],
        lock_result: bool = True,
    ) -> dict[int, PartialModel]: ...

    @abstractmethod
    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: list[str],
        lock_result: bool = True,
    ) -> dict[int, PartialModel]: ...

    @abstractmethod
    def exists(
        self,
        collection: Collection,
        filter: Filter,
        lock_result: bool = True,
    ) -> bool: ...

    @abstractmethod
    def count(
        self,
        collection: Collection,
        filter: Filter,
        lock_result: bool = True,
    ) -> int: ...

    @abstractmethod
    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        lock_result: bool = True,
    ) -> int | None: ...

    @abstractmethod
    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        lock_result: bool = True,
    ) -> int | None: ...

    @abstractmethod
    def history_information(self, fqids: list[str]) -> dict[str, list[dict]]: ...

    @abstractmethod
    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]: ...

    @abstractmethod
    def reserve_id(self, collection: Collection) -> int: ...

    @abstractmethod
    def write(self, write_requests: list[WriteRequest] | WriteRequest) -> None: ...

    @abstractmethod
    def write_without_events(self, write_request: WriteRequest) -> None: ...

    @abstractmethod
    def truncate_db(self) -> None: ...

    @abstractmethod
    def is_deleted(self, fqid: FullQualifiedId) -> bool: ...

    @abstractmethod
    def reset(self, hard: bool = True) -> None: ...

    @abstractmethod
    def get_everything(self) -> dict[Collection, dict[int, PartialModel]]: ...

    @abstractmethod
    def delete_history_information(self) -> None: ...
