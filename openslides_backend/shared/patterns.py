import re
from typing import List, NewType, Optional, Sequence, Union, cast

KEYSEPARATOR = "/"
DECIMAL_PATTERN = r"^-?(\d|[1-9]\d+)\.\d{6}$"
COLOR_PATTERN = r"^#[0-9a-f]{6}$"

ID_REGEX_PART = r"[1-9]\d*"
ID_REGEX = rf"^{ID_REGEX_PART}$"
POSITIVE_NUMBER_REGEX = rf"^(0|{ID_REGEX_PART})$"

ID_PATTERN = re.compile(ID_REGEX)

COLLECTION_REGEX = r"[a-z]([a-z_]+[a-z]+)?"
ID_REGEX = r"[1-9][0-9]*"
FIELD_REGEX = r"[a-z][a-z0-9_]*\$?[a-z0-9_]*"

COLLECTIONFIELD_PATTERN = re.compile(
    f"^({COLLECTION_REGEX}){KEYSEPARATOR}({FIELD_REGEX})$"
)
FQID_REGEX = KEYSEPARATOR.join(("^[a-z]([a-z_]*[a-z])?", f"{ID_REGEX_PART}$"))

Identifier = Union[int, str, "FullQualifiedId"]
IdentifierList = Union[List[int], List[str], List["FullQualifiedId"]]


_Collection = NewType("_Collection", str)
_FullQualifiedId = NewType("_FullQualifiedId", str)
_FullQualifiedField = NewType("_FullQualifiedField", str)
_CollectionField = NewType("_CollectionField", str)

Collection = Union[str, _Collection]  # "meeting"
FullQualifiedId = Union[str, _FullQualifiedId]  # meeting/5
FullQualifiedField = Union[str, _FullQualifiedField]  # meeting/5/name
CollectionField = Union[str, _CollectionField]  # meeting/name


# methods for FullQualifiedId
def to_fqid(collection: Union[str, Collection], id: Union[int, str]) -> FullQualifiedId:
    return cast(FullQualifiedId, f"{collection}{KEYSEPARATOR}{id}")


def fqid_id(fqid: FullQualifiedId) -> int:
    return int(fqid.split(KEYSEPARATOR)[1])


# alt: fqid_collection
def collection_from_fqid(fqid: FullQualifiedId) -> str:
    return fqid.split(KEYSEPARATOR)[0]


def transform_to_fqids(
    value: Optional[
        Union[
            int,
            str,
            FullQualifiedId,
            Sequence[int],
            Sequence[str],
            Sequence[FullQualifiedId],
        ]
    ],
    collection: Collection,
) -> List[FullQualifiedId]:
    """
    Get the given value as a list of fqids. The list may be empty.
    Transform all to fqids to handle everything in the same fashion.
    """
    id_list: IdentifierList
    if value is None:
        id_list = []  # type: ignore  # see https://github.com/python/mypy/issues/2164
    elif not isinstance(value, list):
        value_arr = cast(IdentifierList, [value])
        id_list = value_arr
    else:
        id_list = value

    fqid_list = []
    for id in id_list:
        if isinstance(id, int):
            fqid_list.append(to_fqid(collection, id))
        else:
            fqid_list.append(cast(FullQualifiedId, id))
    return fqid_list


# methods for FullQualifiedField
def to_fqfield(
    collection: Union[str, Collection], id: Union[int, str], field: str
) -> FullQualifiedField:
    return cast(
        FullQualifiedField, f"{collection}{KEYSEPARATOR}{id}{KEYSEPARATOR}{field}"
    )


def fqfield_fqid(fqfield: FullQualifiedField) -> FullQualifiedId:
    collection, id_, _ = str(fqfield).split(KEYSEPARATOR)
    return cast(FullQualifiedId, f"{collection}{KEYSEPARATOR}{id_}")


def fqfield_collection(fqfield: FullQualifiedField) -> Collection:
    return cast(Collection, str(fqfield).split(KEYSEPARATOR)[0])


def fqfield_id(fqfield: FullQualifiedField) -> int:
    return int(str(fqfield).split(KEYSEPARATOR)[1])


def fqfield_field(fqfield: FullQualifiedField) -> str:
    return str(fqfield).split(KEYSEPARATOR)[2]


# methods for CollectionField
def collectionfield_from_collection_and_field(collection: str, field: str) -> str:
    return f"{collection}{KEYSEPARATOR}{field}"


def collectionfield_from_fqid_and_field(fqid: str, field: str) -> str:
    return f"{collection_from_fqid(fqid)}{KEYSEPARATOR}{field}"
