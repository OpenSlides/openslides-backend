import re
from collections.abc import Sequence
from typing import NewType, Union, cast

from datastore.shared.util.key_types import _collection_regex, _field_regex, _id_regex

KEYSEPARATOR = "/"

# Global regexes
ID_REGEX = rf"^{_id_regex}$"
FQID_REGEX_PART = rf"{_collection_regex}{KEYSEPARATOR}{_id_regex}"
FQID_REGEX = rf"^{FQID_REGEX_PART}$"
COLLECTIONFIELD_REGEX = f"^({_collection_regex}){KEYSEPARATOR}({_field_regex})$"

# Specific regexes for fields etc.
DECIMAL_REGEX = r"^-?(\d|[1-9]\d+)\.\d{6}$"
COLOR_REGEX = r"^#[0-9a-f]{6}$"
POSITIVE_NUMBER_REGEX = rf"^(0|{_id_regex})$"
EXTENSION_REFERENCE_IDS_REGEX = rf"\[(?P<fqid>{FQID_REGEX_PART})\]"

# Regexes as patterns
ID_PATTERN = re.compile(ID_REGEX)
COLLECTIONFIELD_PATTERN = re.compile(COLLECTIONFIELD_REGEX)
DECIMAL_PATTERN = re.compile(DECIMAL_REGEX)
COLOR_PATTERN = re.compile(COLOR_REGEX)
EXTENSION_REFERENCE_IDS_PATTERN = re.compile(EXTENSION_REFERENCE_IDS_REGEX)

Identifier = Union[int, str, "FullQualifiedId"]
IdentifierList = Union[list[int], list[str], list["FullQualifiedId"]]

_Collection = NewType("_Collection", str)
_FullQualifiedId = NewType("_FullQualifiedId", str)
_FullQualifiedField = NewType("_FullQualifiedField", str)
_CollectionField = NewType("_CollectionField", str)

Collection = Union[str, _Collection]  # "meeting"
FullQualifiedId = Union[str, _FullQualifiedId]  # meeting/5
FullQualifiedField = Union[str, _FullQualifiedField]  # meeting/5/name
CollectionField = Union[str, _CollectionField]  # meeting/name


def transform_to_fqids(
    value: None | (
        int
        | str
        | FullQualifiedId
        | Sequence[int]
        | Sequence[str]
        | Sequence[FullQualifiedId]
    ),
    collection: Collection,
) -> list[FullQualifiedId]:
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
            fqid_list.append(fqid_from_collection_and_id(collection, id))
        else:
            fqid_list.append(cast(FullQualifiedId, id))
    return fqid_list


def collectionfield_from_collection_and_field(collection: str, field: str) -> str:
    return f"{collection}{KEYSEPARATOR}{field}"


def collectionfield_from_fqid_and_field(fqid: str, field: str) -> str:
    return f"{collection_from_fqid(fqid)}{KEYSEPARATOR}{field}"


def fqfield_from_collection_and_id_and_field(
    collection: Collection, id: int, field: str
) -> FullQualifiedField:
    return cast(
        FullQualifiedField, f"{collection}{KEYSEPARATOR}{id}{KEYSEPARATOR}{field}"
    )


def fqfield_from_fqid_and_field(fqid: str, field: str) -> str:
    return f"{fqid}{KEYSEPARATOR}{field}"


def collection_from_fqfield(fqfield: str) -> str:
    return str(fqfield).split(KEYSEPARATOR)[0]


def fqid_from_fqfield(fqfield: str) -> str:
    return collectionfield_and_fqid_from_fqfield(fqfield)[1]


def field_from_fqfield(fqfield: str) -> str:
    return fqfield.split(KEYSEPARATOR)[2]


def field_from_collectionfield(collectionfield: str) -> str:
    return collectionfield.split(KEYSEPARATOR)[1]


def id_from_fqid(fqid: str) -> int:
    return int(fqid.split(KEYSEPARATOR)[1])


def id_from_fqfield(fqfield: FullQualifiedField) -> int:
    return int(str(fqfield).split(KEYSEPARATOR)[1])


def fqid_and_field_from_fqfield(fqfield: str) -> tuple[str, str]:
    return cast(tuple[str, str], fqfield.rsplit(KEYSEPARATOR, 1))


def collectionfield_and_fqid_from_fqfield(fqfield: str) -> tuple[str, str]:
    parts = fqfield.split(KEYSEPARATOR)
    return f"{parts[0]}{KEYSEPARATOR}{parts[2]}", f"{parts[0]}{KEYSEPARATOR}{parts[1]}"


def collection_from_fqid(fqid: str) -> str:
    return fqid.split(KEYSEPARATOR)[0]


def collection_and_id_from_fqid(fqid: str) -> tuple[str, int]:
    s = fqid.split(KEYSEPARATOR)
    return s[0], int(s[1])


def collection_from_collectionfield(collectionfield: str) -> str:
    return collectionfield.split(KEYSEPARATOR)[0]


def fqid_from_collection_and_id(collection: str, id: str | int) -> str:
    return f"{collection}{KEYSEPARATOR}{id}"
