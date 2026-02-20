from abc import abstractmethod
from collections.abc import Sequence
from typing import Protocol

from openslides_backend.shared.interfaces.collection_field_lock import (
    CollectionFieldLock,
)
from openslides_backend.shared.typing import LockResult, PartialModel

from ...shared.filters import Filter
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection, FullQualifiedId, Id
from .commands import GetManyRequest

MappedFieldsPerFqid = dict[FullQualifiedId, list[str]]

# Max lengths of the important key parts:
# collection: 32
# id: 16
# field: 207
# -> collection + id + field = 255
COLLECTION_MAX_LEN = 32
FQID_MAX_LEN = 48  # collection + id
COLLECTIONFIELD_MAX_LEN = 239  # collection + field


class Database(Protocol):
    """
    Database defines the interface to the database.
    """

    locked_fields: dict[str, CollectionFieldLock]

    @abstractmethod
    def apply_changed_model(
        self, fqid: FullQualifiedId, instance: PartialModel, replace: bool = False
    ) -> None: ...

    @abstractmethod
    def apply_to_be_deleted(self, fqid: FullQualifiedId) -> None: ...

    @abstractmethod
    def apply_to_be_deleted_for_protected(self, fqid: FullQualifiedId) -> None: ...

    @abstractmethod
    def get_changed_model(
        self, collection_or_fqid: str, id_: Id | None = None
    ) -> PartialModel: ...

    @abstractmethod
    def get_changed_models(self, collection: str) -> dict[Id, PartialModel]: ...

    @abstractmethod
    def is_to_be_deleted(self, fqid: FullQualifiedId) -> bool: ...

    @abstractmethod
    def is_to_be_deleted_for_protected(self, fqid: FullQualifiedId) -> bool: ...

    @abstractmethod
    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: list[str],
        lock_result: LockResult = True,
        use_changed_models: bool = True,
        raise_exception: bool = True,
    ) -> PartialModel: ...

    @abstractmethod
    def get_many(
        self,
        get_many_requests: list[GetManyRequest],
        lock_result: LockResult = True,
        use_changed_models: bool = True,
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
        filter_: Filter | None,
        mapped_fields: list[str],
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> dict[int, PartialModel]: ...

    @abstractmethod
    def exists(
        self,
        collection: Collection,
        filter_: Filter | None,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> bool: ...

    @abstractmethod
    def count(
        self,
        collection: Collection,
        filter_: Filter | None,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int: ...

    @abstractmethod
    def min(
        self,
        collection: Collection,
        filter_: Filter | None,
        field: str,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None: ...

    @abstractmethod
    def max(
        self,
        collection: Collection,
        filter_: Filter | None,
        field: str,
        lock_result: bool = True,
        use_changed_models: bool = True,
    ) -> int | None: ...

    @abstractmethod
    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]: ...

    @abstractmethod
    def reserve_id(self, collection: Collection) -> int: ...

    @abstractmethod
    def write(
        self, write_requests: list[WriteRequest] | WriteRequest
    ) -> list[FullQualifiedId]: ...

    @abstractmethod
    def truncate_db(self) -> None: ...

    @abstractmethod
    def is_deleted(self, fqid: FullQualifiedId) -> bool: ...

    @abstractmethod
    def is_new(self, fqid: FullQualifiedId) -> bool: ...

    @abstractmethod
    def reset(self, hard: bool = True) -> None: ...

    @abstractmethod
    def get_everything(self) -> dict[Collection, dict[int, PartialModel]]: ...
