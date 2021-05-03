from typing import List, TypedDict, Union

from ..filters import Filter

CollectionFieldLockWithFilter = TypedDict(
    "CollectionFieldLockWithFilter",
    {
        "position": int,
        "filter": Filter,
    },
    total=False,
)
CollectionFieldLock = Union[
    int, CollectionFieldLockWithFilter, List[CollectionFieldLockWithFilter]
]
