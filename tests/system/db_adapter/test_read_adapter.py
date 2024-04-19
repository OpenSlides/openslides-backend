from datastore.reader.core import (
    FilterRequest,
    GetAllRequest,
    GetManyRequest,
    GetManyRequestPart,
    GetRequest,
)
from datastore.shared.util import FilterOperator

from openslides_backend.services.datastore.read_adapter import ReadAdapter

from .base_relational_db_test import BaseRelationalDBTestCase, WritePayload


class TestReadAdapter(BaseRelationalDBTestCase):
    read_adapter: ReadAdapter
    basic_data: WritePayload = {
        "organization": {
            "fields": ["id", "name", "default_language", "theme_id"],
            "rows": [(1, "Orga 1", "en", 1)],
        },
        "theme": {
            "fields": ["id", "name", "accent_500", "primary_500", "warn_500"],
            "rows": [(1, "Theme 1", "#0000ff", "#00ff00", "#ff0000")],
        },
        "committee": {
            "fields": ["id", "name", "description"],
            "rows": [
                (1, "Committee 1", "a"),
                (2, "Committee 2", "b"),
                (3, "Committee 3", "b"),
                (4, "Committee 4", None),
            ],
        },
        "user": {
            "fields": ["id", "username"],
            "rows": [
                (1, "bob"),
                (2, "rob"),
                (3, "tob"),
                (4, "alice"),
            ],
        },
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls.read_adapter = ReadAdapter()

    # ========== test get ==========

    def test_get_basic(self) -> None:
        self.write_data(self.basic_data)
        request = GetRequest(fqid="committee/2", mapped_fields=["id", "name"])
        result = self.read_adapter.get(request)
        assert result == {"id": 2, "name": "Committee 2"}

    def test_get_without_requesting_id(self) -> None:
        self.write_data(self.basic_data)
        request = GetRequest(fqid="committee/2", mapped_fields=["name"])
        result = self.read_adapter.get(request)
        assert result == {"name": "Committee 2"}

    def test_get_non_existant(self) -> None:
        self.write_data(self.basic_data)
        request = GetRequest(fqid="committee/5", mapped_fields=["id", "name"])
        result = self.read_adapter.get(request)
        assert result is None

    def test_get_with_all_fields(self) -> None:
        self.write_data(self.basic_data)
        request = GetRequest(fqid="committee/2")
        result = self.read_adapter.get(request)
        assert result == {
            "id": 2,
            "name": "Committee 2",
            "description": "b",
            "organization_id": 1,
        }

    # ========== test get_many ==========

    def test_get_many_basic(self) -> None:
        self.write_data(self.basic_data)
        request = GetManyRequest(
            [GetManyRequestPart("committee", [2, 3], ["id", "name"])]
        )
        result = self.read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {
            2: {"id": 2, "name": "Committee 2"},
            3: {"id": 3, "name": "Committee 3"},
        }

    def test_get_many_empty_part(self) -> None:
        self.write_data(self.basic_data)
        request = GetManyRequest([GetManyRequestPart("committee", [], ["id", "name"])])
        result = self.read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {}

    def test_get_many_multi_collection(self) -> None:
        self.write_data(self.basic_data)
        request = GetManyRequest(
            [
                GetManyRequestPart("committee", [2, 3], ["id", "name"]),
                GetManyRequestPart("theme", [1], ["accent_500"]),
                GetManyRequestPart("user", [4], ["username"]),
            ]
        )
        result = self.read_adapter.get_many(request)
        assert len(result) == 3
        assert result["committee"] == {
            2: {"id": 2, "name": "Committee 2"},
            3: {"id": 3, "name": "Committee 3"},
        }
        assert result["theme"] == {
            1: {"accent_500": "#0000ff"},
        }
        assert result["user"] == {
            4: {"username": "alice"},
        }

    def test_get_many_complex(self) -> None:
        self.write_data(self.basic_data)
        request = GetManyRequest(
            [
                GetManyRequestPart("committee", [2, 3], ["name"]),
                GetManyRequestPart("committee", [1, 3, 4], ["description"]),
            ]
        )
        result = self.read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {
            1: {"description": "a"},
            2: {"name": "Committee 2"},
            3: {"name": "Committee 3", "description": "b"},
            4: {},
        }

    def test_get_many_two_parts_same_fields(self) -> None:
        self.write_data(self.basic_data)
        request = GetManyRequest(
            [
                GetManyRequestPart("committee", [2, 3], ["name"]),
                GetManyRequestPart("committee", [1, 3, 4], ["name"]),
            ]
        )
        result = self.read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {
            1: {"name": "Committee 1"},
            2: {"name": "Committee 2"},
            3: {"name": "Committee 3"},
            4: {"name": "Committee 4"},
        }

    def test_get_many_all_fields(self) -> None:
        self.write_data(self.basic_data)
        request = GetManyRequest(
            [
                GetManyRequestPart("committee", [2, 3], []),
                GetManyRequestPart("committee", [1, 3, 4], ["description"]),
            ]
        )
        result = self.read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {
            1: {"description": "a"},
            2: {
                "id": 2,
                "name": "Committee 2",
                "description": "b",
                "organization_id": 1,
            },
            3: {
                "id": 3,
                "name": "Committee 3",
                "description": "b",
                "organization_id": 1,
            },
            4: {},
        }

    def test_get_many_unknown_collection(self) -> None:
        self.write_data(self.basic_data)
        request = GetManyRequest(
            [
                GetManyRequestPart("not_a_collection", [2, 3], []),
            ]
        )
        result = self.read_adapter.get_many(request)
        assert len(result) == 1
        assert result["not_a_collection"] == {}

    def test_get_many_wrong_format(self) -> None:
        with self.assertRaises(
            Exception, msg="Fqfield-based get_many request not supported"
        ):
            self.write_data(self.basic_data)
            request = GetManyRequest(["committee/2/id"])
            self.read_adapter.get_many(request)

    # ========== test get_all ==========

    def test_get_all_basic(self) -> None:
        self.write_data(self.basic_data)
        request = GetAllRequest(collection="committee", mapped_fields=["name"])
        result = self.read_adapter.get_all(request)
        assert len(result) == 4
        assert result == {
            1: {"name": "Committee 1"},
            2: {"name": "Committee 2"},
            3: {"name": "Committee 3"},
            4: {"name": "Committee 4"},
        }

    def test_get_all_with_all_fields(self) -> None:
        self.write_data(self.basic_data)
        request = GetAllRequest(collection="committee")
        result = self.read_adapter.get_all(request)
        assert len(result) == 4
        assert result == {
            1: {
                "id": 1,
                "name": "Committee 1",
                "description": "a",
                "organization_id": 1,
            },
            2: {
                "id": 2,
                "name": "Committee 2",
                "description": "b",
                "organization_id": 1,
            },
            3: {
                "id": 3,
                "name": "Committee 3",
                "description": "b",
                "organization_id": 1,
            },
            4: {"id": 4, "name": "Committee 4", "organization_id": 1},
        }

    # ========== test get_everything ==========

    def test_get_everything(self) -> None:
        self.write_data(self.basic_data)
        result = self.read_adapter.get_everything()
        assert len(result) == 4
        assert len(result["organization"]) == 1
        orga_data = {
            "id": 1,
            "name": "Orga 1",
            "default_language": "en",
            "theme_id": 1,
            "committee_ids": [1, 2, 3, 4],
            "theme_ids": [1],
            "user_ids": [1, 2, 3, 4],
        }
        for key in orga_data:
            assert result["organization"][1][key] == orga_data[key]
        for collection in ["theme", "committee", "user"]:
            data = self.basic_data[collection]
            for row in data["rows"]:
                model = {"organization_id": 1}
                for i in range(len(row)):
                    model[data["fields"][i]] = row[i]
                for key in model:
                    assert result[collection][model["id"]].get(key) == model.get(key)

    # ========== test filter ==========

    def test_filter_basic(self) -> None:
        self.write_data(self.basic_data)
        request = FilterRequest(
            collection="committee",
            filter=FilterOperator("description", "=", "b"),
            mapped_fields=["name"],
        )
        result = self.read_adapter.filter(request)
        assert result == {
            2: {"name": "Committee 2"},
            3: {"name": "Committee 3"},
        }

    def test_filter_with_all_fields(self) -> None:
        self.write_data(self.basic_data)
        request = FilterRequest(
            collection="committee",
            filter=FilterOperator("description", "=", "b"),
        )
        result = self.read_adapter.filter(request)
        assert result == {
            2: {"id": 2, "name": "Committee 2", "organization_id": 1, "description": "b"},
            3: {"id": 3, "name": "Committee 3", "organization_id": 1, "description": "b"},
        }
