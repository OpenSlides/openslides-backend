from unittest.mock import Mock

import openslides_backend.services.database as database
import openslides_backend.services.database.commands as commands
from openslides_backend.services.database.adapter.interface import GetManyRequest
from openslides_backend.shared.filters import FilterOperator, Or
from openslides_backend.shared.patterns import Collection, FullQualifiedId

engine = Mock()
log = Mock()

db = database.Adapter(engine, log)


def test_get() -> None:
    fqid = FullQualifiedId(Collection("fakeModel"), 1)
    fields = ["a", "b", "c"]
    command = commands.Get(fqid=fqid, mappedFields=fields)
    engine.get.return_value = {"f": 1, "meta_deleted": False, "meta_position": 1}
    partial_model = db.get(fqid, fields)
    assert command.data == {"fqid": str(fqid), "mapped_fields": fields}
    assert partial_model is not None
    engine.get.assert_called_with(command)


def test_getMany() -> None:
    fields = ["a", "b", "c"]
    fields2 = ["d", "e", "f"]
    collection = Collection("a")
    ids = [1]
    gmr = GetManyRequest(collection, ids, fields)
    command = commands.GetMany([gmr], fields2)
    engine.getMany.return_value = {
        "a/1": {"f": 1, "meta_deleted": False, "meta_position": 1}
    }
    result = db.getMany([gmr], fields2)
    assert result is not None
    assert command.data == {"requests": [gmr.to_dict()], "mapped_fields": fields2}
    engine.getMany.assert_called_with(command)


def test_getManyByFQIDs() -> None:
    fqid = FullQualifiedId(Collection("fakeModel"), 1)
    command = commands.GetManyByFQIDs([fqid])
    engine.getMany.return_value = {
        "a/1": {"f": 1, "meta_deleted": False, "meta_position": 1}
    }
    result = db.getManyByFQIDs([fqid])
    assert result is not None
    assert command.data == {"requests": [str(fqid)]}


def test_getAll() -> None:
    fields = ["a", "b", "c"]
    collection = Collection("a")
    command = commands.GetAll(collection=collection, mapped_fields=fields)
    engine.getAll.return_value = [{"f": 1, "meta_deleted": False, "meta_position": 1}]
    partial_models = db.getAll(collection=collection, mapped_fields=fields)
    assert command.data == {"collection": str(collection), "mapped_fields": fields}
    assert partial_models is not None
    engine.getAll.assert_called_with(command)


def test_simple_filter() -> None:
    collection = Collection("a")
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field=field, value=value, operator=operator)
    command = commands.Filters(collection=collection, filter=filter)
    engine.filter.return_value = [
        {"f": 1, "meta_deleted": False, "meta_position": 1},
        {"f": 1, "meta_deleted": False, "meta_position": 5},
        {"f": 1, "meta_deleted": False, "meta_position": 6},
        {"f": 1, "meta_deleted": False, "meta_position": 7},
    ]
    found = db.filter(collection=collection, filter=filter)
    assert found is not None
    assert command.data == {
        "collection": str(collection),
        "filter": {"field": field, "operator": operator, "value": value},
    }
    engine.filter.called_with(command)


def test_complex_filter() -> None:
    collection = Collection("a")
    filter1 = FilterOperator(field="f", value="1", operator="=")
    filter2 = FilterOperator(field="f", value="3", operator="=")
    or_filter = Or([filter1, filter2])
    command = commands.Filters(collection=collection, filter=or_filter)
    engine.filter.return_value = [
        {"f": 1, "meta_deleted": False, "meta_position": 1},
        {"f": 3, "meta_deleted": False, "meta_position": 4},
        {"f": 1, "meta_deleted": False, "meta_position": 6},
        {"f": 1, "meta_deleted": False, "meta_position": 7},
    ]
    found = db.filter(collection=collection, filter=or_filter)
    assert found is not None
    assert command.data == {
        "collection": str(collection),
        "filter": or_filter.to_dict(),
    }
    engine.filter.called_with(command)


def test_exists() -> None:
    collection = Collection("a")
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field=field, value=value, operator=operator)
    command = commands.Exists(collection=collection, filter=filter)
    engine.exists.return_value = {"exists": True, "position": 1}
    found = db.exists(collection=collection, filter=filter)
    assert found is not None
    assert command.data == {
        "collection": str(collection),
        "filter": {"field": field, "operator": operator, "value": value},
    }
    engine.exists.called_with(command)


def test_count() -> None:
    collection = Collection("a")
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field=field, value=value, operator=operator)
    command = commands.Count(collection=collection, filter=filter)
    engine.count.return_value = {"count": True, "position": 1}
    count = db.count(collection=collection, filter=filter)
    assert count is not None
    assert command.data == {
        "collection": str(collection),
        "filter": {"field": field, "operator": operator, "value": value},
    }
    engine.exists.called_with(command)


def test_min() -> None:
    collection = Collection("a")
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field=field, value=value, operator=operator)
    command = commands.Min(collection=collection, filter=filter, field=field)
    engine.min.return_value = {"min": 1, "position": 1}
    agg = db.min(collection=collection, filter=filter, field=field)
    assert agg is not None
    assert command.data == {
        "collection": str(collection),
        "filter": {"field": field, "operator": operator, "value": value},
        "field": field,
    }
    engine.exists.called_with(command)


def test_max() -> None:
    collection = Collection("a")
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field=field, value=value, operator=operator)
    command = commands.Max(collection=collection, filter=filter, field=field)
    engine.max.return_value = {"max": 1, "position": 1}
    agg = db.max(collection=collection, filter=filter, field=field)
    assert agg is not None
    assert command.data == {
        "collection": str(collection),
        "filter": {"field": field, "operator": operator, "value": value},
        "field": field,
    }
    engine.exists.called_with(command)
