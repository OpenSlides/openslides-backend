import os
from unittest.mock import Mock

import pytest

from openslides_backend.services.datastore.adapter import Adapter
from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.services.datastore.http_engine import HTTPEngine
from openslides_backend.shared.filters import FilterOperator, Or
from openslides_backend.shared.patterns import Collection, FullQualifiedId

log = Mock()
engine = HTTPEngine(
    "http://localhost:8001/internal/datastore/reader",
    "http://localhost:8002/internal/datastore/writer",
    log,
)
db = Adapter(engine, log)

test_context = os.environ.get("TESTCONTEXT")


@pytest.mark.skipif(test_context != "INTEGRATION", reason="integration only")
def test_get() -> None:
    fqid = FullQualifiedId(Collection("a"), 1)
    fields = ["f"]
    partial_model = db.get(fqid, fields)
    assert partial_model["f"] is not None
    assert partial_model is not None


@pytest.mark.skipif(test_context != "INTEGRATION", reason="integration only")
def test_getAll() -> None:
    fields = ["f"]
    collection = Collection("a")
    partial_models = db.getAll(collection=collection, mapped_fields=fields)
    assert isinstance(partial_models, list)
    assert partial_models is not None
    assert len(partial_models) > 0


@pytest.mark.skipif(test_context != "INTEGRATION", reason="integration only")
def test_complex_filter() -> None:
    collection = Collection("a")
    filter1 = FilterOperator(field="f", value="1", operator="=")
    filter2 = FilterOperator(field="f", value="3", operator="=")
    or_filter = Or([filter1, filter2])
    found = db.filter(collection=collection, filter=or_filter)
    assert found is not None
    assert len(found) > 0


@pytest.mark.skipif(test_context != "INTEGRATION", reason="integration only")
def test_exists() -> None:
    collection = Collection("a")
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field=field, value=value, operator=operator)
    found = db.exists(collection=collection, filter=filter)
    assert found is not None
    assert found["exists"]


@pytest.mark.skipif(test_context != "INTEGRATION", reason="integration only")
def test_count() -> None:
    collection = Collection("a")
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field=field, value=value, operator=operator)
    count = db.count(collection=collection, filter=filter)
    assert count is not None
    assert count["count"] > 0


@pytest.mark.skipif(test_context != "INTEGRATION", reason="integration only")
def test_min() -> None:
    collection = Collection("a")
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field=field, value=value, operator=operator)
    agg = db.min(collection=collection, filter=filter, field=field)
    assert agg is not None


@pytest.mark.skipif(test_context != "INTEGRATION", reason="integration only")
def test_max() -> None:
    collection = Collection("a")
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field=field, value=value, operator=operator)
    agg = db.max(collection=collection, filter=filter, field=field)
    assert agg is not None


@pytest.mark.skipif(test_context != "INTEGRATION", reason="integration only")
def test_getMany() -> None:
    gmr = GetManyRequest(Collection("a"), ids=[1, 2], mapped_fields=["f"])
    gmr2 = GetManyRequest(Collection("b"), [1, 2], mapped_fields=["f"])
    result = db.getMany([gmr, gmr2])
    assert result is not None
    assert result["a/1"] is not None
    assert result["a/2"] is not None
    assert result["b/1"] is not None
