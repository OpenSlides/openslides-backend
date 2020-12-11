import re
from typing import Union

KEYSEPARATOR = "/"

ID_REGEX = r"[1-9]\d*"
ID_PATTERN = re.compile(ID_REGEX)


class Collection:
    """
    The first part of a full qualified field (also known as "key"), e. g.
    motion_change_recommendation.
    """

    def __init__(self, collection: str) -> None:
        self.collection = collection

    def __str__(self) -> str:
        return self.collection

    def __repr__(self) -> str:
        return f"Collection({repr(str(self))})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Collection):
            return NotImplemented
        return self.collection == other.collection

    def __hash__(self) -> int:
        return hash(str(self))


class FullQualifiedId:
    """
    Part of a full qualified field (also known as "key"),
    e. g. motion_change_recommendation/42
    """

    REGEX = KEYSEPARATOR.join(("^[a-z]([a-z_]*[a-z])?", "[1-9][0-9]*$"))

    def __init__(self, collection: Collection, id: int) -> None:
        self.collection = collection
        self.id = id

    def __str__(self) -> str:
        return KEYSEPARATOR.join((str(self.collection), str(self.id)))

    def __repr__(self) -> str:
        return f"FullQualifiedId({repr(str(self))})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FullQualifiedId):
            return NotImplemented
        return self.collection == other.collection and self.id == other.id

    def __hash__(self) -> int:
        return hash(str(self))


class FullQualifiedField:
    """
    The key used in the key-value store i. e. the datastore, e. g.
    motion_change_recommendation/42/text
    """

    def __init__(self, collection: Collection, id: int, field: str) -> None:
        self.collection = collection
        self.id = id
        self.field = field

    def __str__(self) -> str:
        return KEYSEPARATOR.join((str(self.collection), str(self.id), self.field))

    def __repr__(self) -> str:
        return f"FullQualifiedField({repr(str(self))})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FullQualifiedField):
            return NotImplemented
        return (
            self.collection == other.collection
            and self.id == other.id
            and self.field == other.field
        )

    def __hash__(self) -> int:
        return hash(str(self))

    @property
    def fqid(self) -> FullQualifiedId:
        return FullQualifiedId(collection=self.collection, id=self.id)


class CollectionField:
    """
    The key used in the key-value store i. e. the datastore, e. g.
    motion/sequence_number
    """

    def __init__(self, collection: Collection, field: str) -> None:
        self.collection = collection
        self.field = field

    def __str__(self) -> str:
        return KEYSEPARATOR.join((str(self.collection), self.field))

    def __repr__(self) -> str:
        return f"CollectionField({repr(str(self))})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CollectionField):
            return NotImplemented
        return self.collection == other.collection and self.field == other.field

    def __hash__(self) -> int:
        return hash(str(self))


def string_to_fqid(fqid: str) -> FullQualifiedId:
    """
    Converts an FQId as a string to a FullQualifiedId object.
    Assumes the string is a valid FQId.
    """
    collection, id = fqid.split(KEYSEPARATOR)
    return FullQualifiedId(Collection(collection), int(id))


def to_fqid(fqid: Union[str, FullQualifiedId]) -> FullQualifiedId:
    if isinstance(fqid, FullQualifiedId):
        return fqid
    return string_to_fqid(fqid)
