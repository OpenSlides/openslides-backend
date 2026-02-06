import re
from collections.abc import Sequence
from typing import Any, NewType, Union, cast

KEYSEPARATOR = "/"

# Partial regexes
_collection_regex = r"[a-z](?:[a-z_]+[a-z]+)?"
_id_regex = r"[1-9][0-9]*"
_field_regex = r"[a-z][a-z0-9_]*\$?[a-z0-9_]*"  # Keep the template field syntax here to enable backend migration tests

# Global regexes
ID_REGEX = rf"^{_id_regex}$"
COLLECTION_REGEX = f"^{_collection_regex}$"
FIELD_REGEX = f"^{_field_regex}$"
FQID_REGEX_PART = rf"{_collection_regex}{KEYSEPARATOR}{_id_regex}"
FQID_REGEX = rf"^{FQID_REGEX_PART}$"
FQFIELD_REGEX = f"^{FQID_REGEX_PART}{KEYSEPARATOR}{_field_regex}$"
COLLECTIONFIELD_REGEX = f"^({_collection_regex}){KEYSEPARATOR}({_field_regex})$"

# Specific regexes for fields etc.
DECIMAL_REGEX = r"^-?(\d|[1-9]\d+)(\.\d{1,6})?$"
COLOR_REGEX = r"^#[0-9a-fA-F]{6}$"
POSITIVE_NUMBER_REGEX = rf"^(0|{_id_regex})$"
EXTENSION_REFERENCE_IDS_REGEX = rf"\[(?P<fqid>{FQID_REGEX_PART})\]"

# Regexes as patterns
ID_PATTERN = re.compile(ID_REGEX)
COLLECTION_PATTERN = re.compile(COLLECTION_REGEX)
FIELD_PATTERN = re.compile(FIELD_REGEX)
FQID_PATTERN = re.compile(FQID_REGEX)
FQFIELD_PATTERN = re.compile(FQFIELD_REGEX)
COLLECTIONFIELD_PATTERN = re.compile(COLLECTIONFIELD_REGEX)

DECIMAL_PATTERN = re.compile(DECIMAL_REGEX)
COLOR_PATTERN = re.compile(COLOR_REGEX)
EXTENSION_REFERENCE_IDS_PATTERN = re.compile(EXTENSION_REFERENCE_IDS_REGEX)

Identifier = Union[int, str, "FullQualifiedId"]
IdentifierList = Union[list[int], list[str], list["FullQualifiedId"]]

_Collection = NewType("_Collection", str)
_Field = NewType("_Field", str)
_Id = NewType("_Id", int)
_FullQualifiedId = NewType("_FullQualifiedId", str)
_FullQualifiedField = NewType("_FullQualifiedField", str)
_CollectionField = NewType("_CollectionField", str)
_Position = NewType("_Position", int)

Collection = Union[str, _Collection]  # "meeting"
Field = Union[str, _Field]  # "name"
Id = Union[int, _Id]  # 5
FullQualifiedId = Union[str, _FullQualifiedId]  # meeting/5
FullQualifiedField = Union[str, _FullQualifiedField]  # meeting/5/name
CollectionField = Union[str, _CollectionField]  # meeting/name
Position = Union[int, _Position]

META_FIELD_PREFIX = "meta"
META_DELETED = f"{META_FIELD_PREFIX}_deleted"
META_POSITION = f"{META_FIELD_PREFIX}_position"


def is_reserved_field(field: Any) -> bool:
    return isinstance(field, str) and field.startswith(META_FIELD_PREFIX)


def strip_reserved_fields(dictionary: dict[str, Any]) -> None:
    for k in list(dictionary.keys()):
        if is_reserved_field(k):
            del dictionary[k]


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
        id_list = []
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


# Existence checks


def is_fqid(value: str) -> bool:
    return bool(FQID_PATTERN.match(value))


def is_fqfield(value: str) -> bool:
    return bool(FQFIELD_PATTERN.match(value))


def is_collectionfield(value: str) -> bool:
    return bool(COLLECTIONFIELD_PATTERN.match(value))


# Parse FQIDs


def collection_from_fqid(fqid: str) -> str:
    return fqid.split(KEYSEPARATOR)[0]


def id_from_fqid(fqid: str) -> int:
    return int(fqid.split(KEYSEPARATOR)[1])


def collection_and_id_from_fqid(fqid: str) -> tuple[str, int]:
    s = fqid.split(KEYSEPARATOR)
    return s[0], int(s[1])


# Build FQIDs


def fqid_from_collection_and_id(collection: str, id: str | int) -> str:
    return f"{collection}{KEYSEPARATOR}{id}"


# Parse FQFields


def collection_from_fqfield(fqfield: str) -> str:
    return str(fqfield).split(KEYSEPARATOR)[0]


def id_from_fqfield(fqfield: FullQualifiedField) -> int:
    return int(str(fqfield).split(KEYSEPARATOR)[1])


def field_from_fqfield(fqfield: str) -> str:
    return fqfield.split(KEYSEPARATOR)[2]


def collection_and_field_from_fqfield(fqfield: str) -> tuple[str, str]:
    parts = fqfield.split(KEYSEPARATOR)
    return parts[0], parts[2]


def fqid_from_fqfield(fqfield: str) -> str:
    return collectionfield_and_fqid_from_fqfield(fqfield)[1]


def fqid_and_field_from_fqfield(fqfield: str) -> tuple[str, str]:
    return cast(tuple[str, str], fqfield.rsplit(KEYSEPARATOR, 1))


def collectionfield_and_fqid_from_fqfield(fqfield: str) -> tuple[str, str]:
    parts = fqfield.split(KEYSEPARATOR)
    return f"{parts[0]}{KEYSEPARATOR}{parts[2]}", f"{parts[0]}{KEYSEPARATOR}{parts[1]}"


# Build FQFields


def fqfield_from_collection_and_id_and_field(
    collection: Collection, id: int, field: str
) -> FullQualifiedField:
    return cast(
        FullQualifiedField, f"{collection}{KEYSEPARATOR}{id}{KEYSEPARATOR}{field}"
    )


def fqfield_from_fqid_and_field(fqid: str, field: str) -> str:
    return f"{fqid}{KEYSEPARATOR}{field}"


# Parse collectionfields


def collection_from_collectionfield(collectionfield: str) -> str:
    return collectionfield.split(KEYSEPARATOR)[0]


def field_from_collectionfield(collectionfield: str) -> str:
    return collectionfield.split(KEYSEPARATOR)[1]


def collection_and_field_from_collectionfield(collectionfield: str) -> tuple[str, str]:
    return cast(tuple[str, str], collectionfield.split(KEYSEPARATOR))


# Build collection fields


def collectionfield_from_collection_and_field(collection: str, field: str) -> str:
    return f"{collection}{KEYSEPARATOR}{field}"


def collectionfield_from_fqid_and_field(fqid: str, field: str) -> str:
    return f"{collection_from_fqid(fqid)}{KEYSEPARATOR}{field}"


class InvalidFormat(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


def assert_string(key: Any) -> None:
    if not isinstance(key, str):
        raise InvalidFormat(
            f"The key `{key}` has type {type(key)}, but string is expected"
        )


class InvalidKeyFormat(InvalidFormat):
    def __init__(self, key: str) -> None:
        super().__init__(f"The key '{key}' is no fqid, fqfield or collectionkey")


class KEY_TYPE:
    FQID = 1
    FQFIELD = 2
    COLLECTIONFIELD = 3


def get_key_type(key: Any) -> Any:
    assert_string(key)

    if FQID_PATTERN.match(key):
        return KEY_TYPE.FQID
    if FQFIELD_PATTERN.match(key):
        return KEY_TYPE.FQFIELD
    if COLLECTIONFIELD_PATTERN.match(key):
        return KEY_TYPE.COLLECTIONFIELD

    raise InvalidKeyFormat(key)


def assert_is_fqid(key: Any) -> None:
    assert_string(key)
    if not FQID_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_fqfield(key: Any) -> None:
    assert_string(key)
    if not FQFIELD_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_collectionfield(key: Any) -> None:
    assert_string(key)
    if not COLLECTIONFIELD_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_collection(key: Any) -> None:
    assert_string(key)
    if not COLLECTION_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_id(key: Any) -> None:
    assert_string(key)
    if not ID_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_field(key: Any) -> None:
    assert_string(key)
    if not FIELD_PATTERN.match(key):
        raise InvalidKeyFormat(key)
