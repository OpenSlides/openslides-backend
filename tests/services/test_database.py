from unittest import TestCase
from unittest.mock import Mock

import simplejson as json

from openslides_backend.services.datastore import commands
from openslides_backend.services.datastore.adapter import Adapter
from openslides_backend.services.datastore.interface import GetManyRequest
from openslides_backend.shared.filters import FilterOperator, Or
from openslides_backend.shared.interfaces import WriteRequestElement
from openslides_backend.shared.patterns import Collection, FullQualifiedId


class DatastoreAdapterTester(TestCase):
    def setUp(self) -> None:
        self.engine = Mock()
        log = Mock()
        self.db = Adapter(self.engine, log)

    def test_get(self) -> None:
        fqid = FullQualifiedId(Collection("fakeModel"), 1)
        fields = ["a", "b", "c"]
        command = commands.Get(fqid=fqid, mappedFields=fields)
        self.engine.retrieve.return_value = (
            json.dumps({"f": 1, "meta_deleted": False, "meta_position": 1}),
            200,
        )
        partial_model = self.db.get(fqid, fields)
        assert command.get_raw_data() == {"fqid": str(fqid), "mapped_fields": fields}
        assert partial_model is not None
        self.engine.retrieve.assert_called_with("get", command.data)

    def test_get_many(self) -> None:
        fields = ["a", "b", "c"]
        collection = Collection("a")
        ids = [1]
        gmr = GetManyRequest(collection, ids, fields)
        command = commands.GetMany([gmr])
        self.engine.retrieve.return_value = (
            json.dumps(
                {"a": {"1": {"c": 1, "meta_deleted": False, "meta_position": 1}}}
            ),
            200,
        )
        result = self.db.get_many([gmr])
        assert result is not None
        assert command.get_raw_data() == {
            "requests": [gmr.to_dict()],
        }
        self.engine.retrieve.assert_called_with("get_many", command.data)

    def test_getAll(self) -> None:
        fields = ["a", "b", "c"]
        collection = Collection("a")
        command = commands.GetAll(collection=collection, mapped_fields=fields)
        self.engine.retrieve.return_value = (
            json.dumps([{"f": 1, "meta_deleted": False, "meta_position": 1}]),
            200,
        )
        partial_models = self.db.get_all(collection=collection, mapped_fields=fields)
        assert command.get_raw_data() == {
            "collection": str(collection),
            "mapped_fields": fields,
        }
        assert partial_models is not None
        self.engine.retrieve.assert_called_with("get_all", command.data)

    def test_simple_filter(self) -> None:
        collection = Collection("a")
        field = "f"
        value = "1"
        operator = "="
        filter = FilterOperator(field=field, value=value, operator=operator)
        command = commands.Filter(collection=collection, filter=filter)
        self.engine.retrieve.return_value = (
            json.dumps(
                [
                    {"f": 1, "meta_deleted": False, "meta_position": 1},
                    {"f": 1, "meta_deleted": False, "meta_position": 5},
                    {"f": 1, "meta_deleted": False, "meta_position": 6},
                    {"f": 1, "meta_deleted": False, "meta_position": 7},
                ]
            ),
            200,
        )
        found = self.db.filter(collection=collection, filter=filter)
        assert found is not None
        assert command.get_raw_data() == {
            "collection": str(collection),
            "filter": {"field": field, "operator": operator, "value": value},
        }
        self.engine.retrieve.called_with("filter", command.data)

    def test_complex_filter(self) -> None:
        collection = Collection("a")
        filter1 = FilterOperator(field="f", value="1", operator="=")
        filter2 = FilterOperator(field="f", value="3", operator="=")
        or_filter = Or([filter1, filter2])
        command = commands.Filter(collection=collection, filter=or_filter)
        self.engine.retrieve.return_value = (
            json.dumps(
                [
                    {"f": 1, "meta_deleted": False, "meta_position": 1},
                    {"f": 3, "meta_deleted": False, "meta_position": 4},
                    {"f": 1, "meta_deleted": False, "meta_position": 6},
                    {"f": 1, "meta_deleted": False, "meta_position": 7},
                ]
            ),
            200,
        )
        found = self.db.filter(collection=collection, filter=or_filter)
        assert found is not None
        assert command.get_raw_data() == {
            "collection": str(collection),
            "filter": or_filter.to_dict(),
        }
        self.engine.retrieve.called_with("filter", command.data)

    def test_exists(self) -> None:
        collection = Collection("a")
        field = "f"
        value = "1"
        operator = "="
        filter = FilterOperator(field=field, value=value, operator=operator)
        command = commands.Exists(collection=collection, filter=filter)
        self.engine.retrieve.return_value = (
            json.dumps({"exists": True, "position": 1}),
            200,
        )
        found = self.db.exists(collection=collection, filter=filter)
        assert found is not None
        assert command.get_raw_data() == {
            "collection": str(collection),
            "filter": {"field": field, "operator": operator, "value": value},
        }
        self.engine.retrieve.called_with("exists", command.data)

    def test_count(self) -> None:
        collection = Collection("a")
        field = "f"
        value = "1"
        operator = "="
        filter = FilterOperator(field=field, value=value, operator=operator)
        command = commands.Count(collection=collection, filter=filter)
        self.engine.retrieve.return_value = (
            json.dumps({"count": True, "position": 1}),
            200,
        )
        count = self.db.count(collection=collection, filter=filter)
        assert count is not None
        assert command.get_raw_data() == {
            "collection": str(collection),
            "filter": {"field": field, "operator": operator, "value": value},
        }
        self.engine.retrieve.called_with("count", command.data)

    def test_min(self) -> None:
        collection = Collection("a")
        field = "f"
        value = "1"
        operator = "="
        filter = FilterOperator(field=field, value=value, operator=operator)
        command = commands.Min(collection=collection, filter=filter, field=field)
        self.engine.retrieve.return_value = json.dumps({"min": 1, "position": 1}), 200
        agg = self.db.min(collection=collection, filter=filter, field=field)
        assert agg is not None
        assert command.get_raw_data() == {
            "collection": str(collection),
            "filter": {"field": field, "operator": operator, "value": value},
            "field": field,
        }
        self.engine.retrieve.called_with("min", command.data)

    def test_max(self) -> None:
        collection = Collection("a")
        field = "f"
        value = "1"
        operator = "="
        filter = FilterOperator(field=field, value=value, operator=operator)
        command = commands.Max(collection=collection, filter=filter, field=field)
        self.engine.retrieve.return_value = json.dumps({"max": 1, "position": 1}), 200
        agg = self.db.max(collection=collection, filter=filter, field=field)
        assert agg is not None
        assert command.get_raw_data() == {
            "collection": str(collection),
            "filter": {"field": field, "operator": operator, "value": value},
            "field": field,
        }
        self.engine.retrieve.called_with("max", command.data)

    def test_reserve_ids(self) -> None:
        collection = Collection("fakeModel")
        command = commands.ReserveIds(collection=collection, amount=1)
        self.engine.retrieve.return_value = json.dumps({"ids": [42]}), 200
        # Attention: We call reserve_id here not reserve_ids. This is nice.
        new_id = self.db.reserve_id(collection=collection)
        assert command.get_raw_data() == {"collection": str(collection), "amount": 1}
        self.engine.retrieve.assert_called_with("reserve_ids", command.data)
        assert new_id == 42

    def test_write(self) -> None:
        write_request: WriteRequestElement = {
            "events": [],
            "information": {},
            "user_id": 42,
        }
        command = commands.Write(write_request=write_request, locked_fields={})
        self.engine.retrieve.return_value = "", 200
        self.db.write(write_requests=[write_request])
        assert (
            command.data
            == '{"events": [], "information": {}, "user_id": 42, "locked_fields": {}}'
        )
