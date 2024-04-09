
from openslides_backend.shared.patterns import (
    COLLECTION_PATTERN,
    COLLECTIONFIELD_PATTERN,
    FIELD_PATTERN,
    FQFIELD_PATTERN,
    FQID_PATTERN,
    ID_PATTERN,
)

from .exceptions import InvalidFormat


class InvalidKeyFormat(InvalidFormat):
    def __init__(self, key):
        super().__init__(f"The key '{key}' is no fqid, fqfield or collectionkey")


class KEY_TYPE:
    FQID = 1
    FQFIELD = 2
    COLLECTIONFIELD = 3


def assert_string(key):
    if not isinstance(key, str):
        raise InvalidFormat(
            f"The key `{key}` has type {type(key)}, but string is expected"
        )


def get_key_type(key):
    assert_string(key)

    if FQID_PATTERN.match(key):
        return KEY_TYPE.FQID
    if FQFIELD_PATTERN.match(key):
        return KEY_TYPE.FQFIELD
    if COLLECTIONFIELD_PATTERN.match(key):
        return KEY_TYPE.COLLECTIONFIELD

    raise InvalidKeyFormat(key)


def assert_is_fqid(key):
    assert_string(key)
    if not FQID_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_fqfield(key):
    assert_string(key)
    if not FQFIELD_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_collectionfield(key):
    assert_string(key)
    if not COLLECTIONFIELD_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_collection(key):
    assert_string(key)
    if not COLLECTION_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_id(key):
    assert_string(key)
    if not ID_PATTERN.match(key):
        raise InvalidKeyFormat(key)


def assert_is_field(key):
    assert_string(key)
    if not FIELD_PATTERN.match(key):
        raise InvalidKeyFormat(key)
