from typing import TypedDict, Union

from ..filters import Filter

CollectionFieldLockWithFilter = TypedDict(
    "CollectionFieldLockWithFilter",
    {
        "position": int,
        "filter": Filter,
    },
)
CollectionFieldLock = Union[int, CollectionFieldLockWithFilter]
