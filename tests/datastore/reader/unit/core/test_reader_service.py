from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.reader.core import Reader
from openslides_backend.datastore.reader.core.reader_service import ReaderService
from openslides_backend.datastore.reader.core.requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetEverythingRequest,
    GetManyRequest,
    GetManyRequestPart,
    GetRequest,
    MinMaxRequest,
)
from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler
from openslides_backend.datastore.shared.postgresql_backend.sql_read_database_backend_service import (
    SqlReadDatabaseBackendService,
)
from openslides_backend.datastore.shared.services import (
    EnvironmentService,
    ReadDatabase,
)
from openslides_backend.datastore.shared.services.read_database import (
    AggregateFilterQueryFieldsParameters,
    CountFilterQueryFieldsParameters,
)
from openslides_backend.datastore.shared.util import (
    DeletedModelsBehaviour,
    ModelDoesNotExist,
    ModelNotDeleted,
)
from openslides_backend.shared.filters import FilterOperator
from tests.datastore import reset_di  # noqa


@pytest.fixture(autouse=True)
def provide_di(reset_di):  # noqa
    injector.register_as_singleton(ConnectionHandler, MagicMock)
    injector.register_as_singleton(ReadDatabase, MagicMock)
    injector.register(Reader, ReaderService)
    injector.register(EnvironmentService, EnvironmentService)
    yield


@pytest.fixture()
def reader(provide_di):
    yield injector.get(Reader)


@pytest.fixture()
def read_db(provide_di):
    yield injector.get(ReadDatabase)


def test_get(reader: ReaderService, read_db: SqlReadDatabaseBackendService):
    model = MagicMock()
    read_db.get = get = MagicMock(return_value=model)

    request = GetRequest("c/1", ["field"])

    assert reader.get(request) == model

    get.assert_called_once()
    ca = get.call_args[0]
    assert ca[0] == "c/1"
    assert ca[1].per_fqid == {"c/1": ["field"]}
    assert ca[2] == DeletedModelsBehaviour.NO_DELETED


def test_get_with_position(
    reader: ReaderService, read_db: SqlReadDatabaseBackendService
):
    fqid = "c/1"
    model = MagicMock()
    reader.filter_fqids_by_deleted_status = MagicMock(return_value=[fqid])
    read_db.build_model_ignore_deleted = bmid = MagicMock(return_value=model)
    reader.apply_mapped_fields = amf = MagicMock(return_value=model)

    request = GetRequest(fqid, ["field"], 42)

    assert reader.get(request) == model

    bmid.assert_called_with(fqid, 42)
    amf.assert_called_with(model, ["field"])


def test_get_with_position_deleted_no_deleted(reader, read_db):
    reader.filter_fqids_by_deleted_status = MagicMock(return_value=[])

    request = GetRequest("c/1", ["field"], 42, DeletedModelsBehaviour.NO_DELETED)
    with pytest.raises(ModelDoesNotExist):
        reader.get(request)


def test_get_with_position_not_deleted_only_deleted(reader, read_db):
    reader.filter_fqids_by_deleted_status = MagicMock(return_value=[])

    request = GetRequest("c/1", ["field"], 42, DeletedModelsBehaviour.ONLY_DELETED)
    with pytest.raises(ModelNotDeleted):
        reader.get(request)


def test_get_many(reader: ReaderService, read_db: SqlReadDatabaseBackendService):
    model = MagicMock()
    result = {"c/1": model}
    read_db.get_many = get_many = MagicMock(return_value=result)

    parts = [
        GetManyRequestPart("a", "1", ["field1"]),
        GetManyRequestPart("b", "1", ["field2"]),
    ]
    request = GetManyRequest(parts, ["field"])

    assert reader.get_many(request) == {"a": {}, "b": {}, "c": {1: model}}

    get_many.assert_called_once()
    ca = get_many.call_args[0]
    assert ca[0] == ["a/1", "b/1"]
    assert ca[1].per_fqid == {"a/1": ["field1", "field"], "b/1": ["field2", "field"]}
    assert ca[2] == DeletedModelsBehaviour.NO_DELETED


def test_get_many_with_position(
    reader: ReaderService, read_db: SqlReadDatabaseBackendService
):
    model = MagicMock()
    result = {"c/1": model}
    deleted_map = {"a/1": False, "b/1": False}
    read_db.get_deleted_status = gds = MagicMock(return_value=deleted_map)
    read_db.build_models_ignore_deleted = bmid = MagicMock(return_value=result)
    reader.apply_mapped_fields_multi = amfm = MagicMock(return_value=result)

    parts = [
        GetManyRequestPart("a", "1", ["field1"]),
        GetManyRequestPart("b", "1", ["field2"]),
    ]
    request = GetManyRequest(parts, ["field"], 42)

    assert reader.get_many(request) == {"a": {}, "b": {}, "c": {1: model}}

    gds.assert_called_with(["a/1", "b/1"], 42)
    bmid.assert_called_with(["a/1", "b/1"], 42)
    amfm.assert_called_with(
        result, {"a/1": ["field1", "field"], "b/1": ["field2", "field"]}
    )


def test_get_many_with_position_deleted_no_deleted(
    reader: ReaderService, read_db: SqlReadDatabaseBackendService
):
    deleted_map = {"a/1": True, "b/1": False}
    read_db.get_deleted_status = gds = MagicMock(return_value=deleted_map)
    read_db.build_models_ignore_deleted = bmid = MagicMock()
    reader.apply_mapped_fields_multi = MagicMock()

    parts = [
        GetManyRequestPart("a", "1", ["field1"]),
        GetManyRequestPart("b", "1", ["field2"]),
    ]
    request = GetManyRequest(parts, ["field"], 42)

    reader.get_many(request)

    gds.assert_called_with(["a/1", "b/1"], 42)
    bmid.assert_called_with(["b/1"], 42)


def test_get_many_with_position_not_deleted_only_deleted(
    reader: ReaderService, read_db: SqlReadDatabaseBackendService
):
    deleted_map = {"a/1": True, "b/1": False}
    read_db.get_deleted_status = gds = MagicMock(return_value=deleted_map)
    read_db.build_models_ignore_deleted = bmid = MagicMock()
    reader.apply_mapped_fields_multi = MagicMock()

    parts = [
        GetManyRequestPart("a", "1", ["field1"]),
        GetManyRequestPart("b", "1", ["field2"]),
    ]
    request = GetManyRequest(parts, ["field"], 42, DeletedModelsBehaviour.ONLY_DELETED)

    reader.get_many(request)

    gds.assert_called_with(["a/1", "b/1"], 42)
    bmid.assert_called_with(["a/1"], 42)


def test_get_all(reader: ReaderService, read_db: SqlReadDatabaseBackendService):
    result = MagicMock()
    read_db.get_all = get_all = MagicMock(return_value=result)

    request = GetAllRequest("collection", ["field"])

    assert reader.get_all(request) == result

    get_all.assert_called()


def test_get_everything(reader: ReaderService, read_db: SqlReadDatabaseBackendService):
    result = MagicMock()
    read_db.get_everything = get_everything = MagicMock(return_value=result)

    request = GetEverythingRequest(DeletedModelsBehaviour.ALL_MODELS)

    assert reader.get_everything(request) == result

    get_everything.assert_called_with(DeletedModelsBehaviour.ALL_MODELS)


def test_filter(reader: ReaderService, read_db: SqlReadDatabaseBackendService):
    result = MagicMock()
    read_db.filter = filter = MagicMock(return_value=result)
    read_db.get_max_position = get_pos = MagicMock(return_value=42)

    filter_operator = FilterOperator("field", "=", "data")
    request = FilterRequest("collection", filter_operator, ["field"])

    assert reader.filter(request) == {"data": result, "position": 42}

    filter.assert_called_with("collection", filter_operator, ["field"])
    get_pos.assert_called()


def test_exists_true(reader: ReaderService):
    reader.count = count = MagicMock(return_value={"count": 1, "position": 0})

    filter_operator = FilterOperator("field", "=", "data")
    request = AggregateRequest("collection", filter_operator)

    assert reader.exists(request) == {"exists": True, "position": 0}

    count.assert_called_with(request)


def test_exists_false(reader: ReaderService):
    reader.count = count = MagicMock(return_value={"count": 0, "position": 0})

    filter_operator = FilterOperator("field", "=", "data")
    request = AggregateRequest("collection", filter_operator)

    assert reader.exists(request) == {"exists": False, "position": 0}

    count.assert_called_with(request)


def test_count(reader: ReaderService, read_db: SqlReadDatabaseBackendService):
    result = MagicMock()
    read_db.aggregate = aggregate = MagicMock(return_value=result)

    filter_operator = FilterOperator("field", "=", "data")
    request = AggregateRequest("collection", filter_operator)

    assert reader.count(request) == result

    aggregate.assert_called_with(
        "collection", filter_operator, CountFilterQueryFieldsParameters()
    )


def test_min(reader: ReaderService, read_db: SqlReadDatabaseBackendService):
    result = MagicMock()
    read_db.aggregate = aggregate = MagicMock(return_value=result)

    filter_operator = FilterOperator("field", "=", "data")
    request = MinMaxRequest("collection", filter_operator, "field")
    params = AggregateFilterQueryFieldsParameters("min", "field", "int")

    assert reader.min(request) == result

    aggregate.assert_called_with("collection", filter_operator, params)


def test_max(reader: ReaderService, read_db: SqlReadDatabaseBackendService):
    result = MagicMock()
    read_db.aggregate = aggregate = MagicMock(return_value=result)

    filter_operator = FilterOperator("field", "=", "data")
    request = MinMaxRequest("collection", filter_operator, "field")
    params = AggregateFilterQueryFieldsParameters("max", "field", "int")

    assert reader.max(request) == result

    aggregate.assert_called_with("collection", filter_operator, params)


def test_filter_fqids_by_deleted_status(reader: ReaderService):
    fqids = MagicMock()
    res = reader.filter_fqids_by_deleted_status(
        fqids, 42, DeletedModelsBehaviour.ALL_MODELS
    )
    assert res == fqids


def test_apply_mapped_fields(reader: ReaderService):
    model = {"f1": "a", "f2": "b"}
    assert reader.apply_mapped_fields(model, ["f1"]) == {"f1": "a"}


def test_apply_mapped_fields_no_fields(reader: ReaderService):
    model = MagicMock()
    assert reader.apply_mapped_fields(model, []) == model


def test_apply_mapped_fields_multi(reader: ReaderService):
    result = {
        "a/1": {"f1": "a", "f2": "b", "f": "c"},
        "b/1": {"f3": "a", "f4": "b", "f": "c"},
    }
    assert reader.apply_mapped_fields_multi(
        result, {"a/1": ["f1", "f"], "b/1": ["f3", "f"]}
    ) == {"a/1": {"f1": "a", "f": "c"}, "b/1": {"f3": "a", "f": "c"}}


def test_apply_mapped_fields_multi_no_fields(reader: ReaderService):
    result = MagicMock()
    assert reader.apply_mapped_fields_multi(result, {}) == result
