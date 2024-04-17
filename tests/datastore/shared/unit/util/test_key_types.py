import pytest

from openslides_backend.datastore.shared.util import (
    KEY_TYPE,
    InvalidFormat,
    InvalidKeyFormat,
    assert_is_collection,
    assert_is_collectionfield,
    assert_is_field,
    assert_is_fqfield,
    assert_is_fqid,
    assert_is_id,
    assert_string,
    get_key_type,
)


def test_no_string_1():
    with pytest.raises(InvalidFormat):
        get_key_type(None)


def test_no_string_2():
    with pytest.raises(InvalidFormat):
        get_key_type(1337)


def test_no_string_3():
    with pytest.raises(InvalidFormat):
        get_key_type(range(42))


def test_empty_string():
    with pytest.raises(InvalidKeyFormat):
        get_key_type("")


def test_fqid():
    assert get_key_type("my_collection_withunderscore/1") == KEY_TYPE.FQID


def test_fqfield():
    assert get_key_type("collection/493/my_field_2_") == KEY_TYPE.FQFIELD


def test_collectionfield():
    assert get_key_type("collection/some_42_field_0") == KEY_TYPE.COLLECTIONFIELD


def no_valid_key_type(key):
    with pytest.raises(InvalidKeyFormat):
        get_key_type(key)


no_fqids = (
    "_collection/482",
    "collection_/482",
    "collection/0",
    "collection/96e2",
    "collection/1$2",
    "collection_/593",
    "some string without a slash",
    "collection$string/1",
    "collection1/1",
)
no_fqfields = (
    "collection/493/_field",
    "_collection/493/field",
    "collection/493/_field",
    "collection/29/1field",
    "collection/1/$field",
    "collection/1/field_$_$_suffix",
)
no_collectionfields = (
    "_collection/field",
    "collection/4_field",
    "collection/my_\u0394_unicode_field",
    "collection/$field",
    "collection/field_$_$_suffix",
)

all_keys = no_fqids + no_fqfields + no_collectionfields


def test_get_key_type_error():
    for fqid in all_keys:
        no_valid_key_type(fqid)


def test_assert_string_none():
    with pytest.raises(InvalidFormat):
        assert_string(None)


def test_assert_errors():
    for fqid in all_keys:
        with pytest.raises(InvalidKeyFormat):
            assert_is_fqid(fqid)
        with pytest.raises(InvalidKeyFormat):
            assert_is_fqfield(fqid)
        with pytest.raises(InvalidKeyFormat):
            assert_is_collectionfield(fqid)


def test_no_collection():
    for c in ("12312", "_collection"):
        with pytest.raises(InvalidKeyFormat):
            assert_is_collection(c)


def test_no_field():
    for f in ("1wefwef", "_field"):
        with pytest.raises(InvalidKeyFormat):
            assert_is_field(f)


def test_no_id():
    for id in ("-12312", "string"):
        with pytest.raises(InvalidKeyFormat):
            assert_is_id(id)


def test_collection():
    assert_is_collection("my_collection")


def test_collection_fail():
    with pytest.raises(InvalidKeyFormat):
        assert_is_collection("not valid")


def test_id():
    assert_is_id("13942")


def test_field():
    assert_is_field("my_field_2_")
