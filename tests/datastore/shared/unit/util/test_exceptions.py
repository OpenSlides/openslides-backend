from openslides_backend.datastore.shared.util import (
    DatastoreNotEmpty,
    InvalidDatastoreState,
    InvalidFormat,
    ModelDoesNotExist,
    ModelExists,
    ModelLocked,
    ModelNotDeleted,
)


def test_invalid_format():
    e = InvalidFormat("msg")
    assert e.msg == "msg"


def test_model_does_not_exist():
    e = ModelDoesNotExist("fqid")
    assert e.fqid == "fqid"


def test_model_exists():
    e = ModelExists("fqid")
    assert e.fqid == "fqid"


def test_model_not_deleted():
    e = ModelNotDeleted("fqid")
    assert e.fqid == "fqid"


def test_model_locked():
    e = ModelLocked(["key"])
    assert e.keys == ["key"]


def test_invalid_datastore_state():
    e = InvalidDatastoreState("msg")
    assert e.msg == "msg"


def test_datastore_not_empty():
    e = DatastoreNotEmpty("msg")
    assert e.msg == "msg"
