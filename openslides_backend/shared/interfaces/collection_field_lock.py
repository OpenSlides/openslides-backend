from typing import TypedDict, Union

from ..filters import Filter


class CollectionFieldLockWithFilter(TypedDict, total=False):
    position: int
    filter: Filter


CollectionFieldLock = Union[
    int, CollectionFieldLockWithFilter, list[CollectionFieldLockWithFilter]
]
