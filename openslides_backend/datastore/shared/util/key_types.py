import re

from .exceptions import InvalidFormat
from .key_strings import KEYSEPARATOR


class InvalidKeyFormat(InvalidFormat):
    def __init__(self, key):
        super().__init__(f"The key '{key}' is no fqid, fqfield or collectionkey")


class KEY_TYPE:
    FQID = 1
    FQFIELD = 2
    COLLECTIONFIELD = 3


_collection_regex = r"[a-z](?:[a-z_]+[a-z]+)?"
_id_regex = r"[1-9][0-9]*"
_field_regex = r"[a-z][a-z0-9_]*\$?[a-z0-9_]*"  # Keep the template field syntax here to enable backend migration tests

fqid_regex = re.compile(f"^({_collection_regex}){KEYSEPARATOR}({_id_regex})$")
fqfield_regex = re.compile(
    f"^({_collection_regex}){KEYSEPARATOR}({_id_regex}){KEYSEPARATOR}({_field_regex})$"
)
collectionfield_regex = re.compile(
    f"^({_collection_regex}){KEYSEPARATOR}({_field_regex})$"
)

id_regex = re.compile(f"^{_id_regex}$")
collection_regex = re.compile(f"^{_collection_regex}$")
field_regex = re.compile(f"^{_field_regex}$")


def assert_string(key):
    if not isinstance(key, str):
        raise InvalidFormat(
            f"The key `{key}` has type {type(key)}, but string is expected"
        )


def get_key_type(key):
    assert_string(key)

    if fqid_regex.match(key):
        return KEY_TYPE.FQID
    if fqfield_regex.match(key):
        return KEY_TYPE.FQFIELD
    if collectionfield_regex.match(key):
        return KEY_TYPE.COLLECTIONFIELD

    raise InvalidKeyFormat(key)


def assert_is_fqid(key):
    assert_string(key)
    if not fqid_regex.match(key):
        raise InvalidKeyFormat(key)


def assert_is_fqfield(key):
    assert_string(key)
    if not fqfield_regex.match(key):
        raise InvalidKeyFormat(key)


def assert_is_collectionfield(key):
    assert_string(key)
    if not collectionfield_regex.match(key):
        raise InvalidKeyFormat(key)


def assert_is_collection(key):
    assert_string(key)
    if not collection_regex.match(key):
        raise InvalidKeyFormat(key)


def assert_is_id(key):
    assert_string(key)
    if not id_regex.match(key):
        raise InvalidKeyFormat(key)


def assert_is_field(key):
    assert_string(key)
    if not field_regex.match(key):
        raise InvalidKeyFormat(key)
