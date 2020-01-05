from typing import Any, Dict, List, Tuple

from typing_extensions import Protocol

from ..utils.types import Collection, FullQualifiedId, Headers


class DatabaseProvider(Protocol):
    def get(self, fqid: FullQualifiedId, mapped_fields: List[str] = None) -> None:
        ...

    def getMany(
        self, collection: Collection, ids: List[int], mapped_fields: List[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        ...

    def getId(self, collection: Collection) -> Tuple[int, int]:
        ...

    # def exists(self, collection: Collection, ids: List[int]) -> None: ...

    # getAll, filter, count, min, max, ...some with deleted or only deleted


class AuthProvider(Protocol):
    def get_user(self, headers: Headers) -> int:
        ...
