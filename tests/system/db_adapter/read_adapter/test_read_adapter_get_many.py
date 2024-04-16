from datastore.reader.core import GetManyRequest, GetManyRequestPart

from openslides_backend.services.datastore.read_adapter import ReadAdapter

from ..base_relational_db_test import BaseRelationalDBTestCase, WritePayload


class TestReadAdapter(BaseRelationalDBTestCase):
    basic_data: list[WritePayload] = [
        {
            "table": "organization_t",
            "fields": ["id", "name", "default_language", "theme_id"],
            "rows": [(1, "Orga 1", "en", 1)],
        },
        {
            "table": "theme_t",
            "fields": ["id", "name", "accent_500", "primary_500", "warn_500"],
            "rows": [(1, "Theme 1", "#0000ff", "#00ff00", "#ff0000")],
        },
        {
            "table": "committee_t",
            "fields": ["id", "name", "description"],
            "rows": [
                (1, "Committee 1", "a"),
                (2, "Committee 2", "b"),
                (3, "Committee 3", "c"),
                (4, "Committee 4", None),
            ],
        },
        {
            "table": "user_t",
            "fields": ["id", "username"],
            "rows": [
                (1, "bob"),
                (2, "rob"),
                (3, "tob"),
                (4, "alice"),
            ],
        },
    ]

    def test_get_many_basic(self) -> None:
        self.write_data(self.basic_data)
        read_adapter = ReadAdapter()
        request = GetManyRequest(
            [GetManyRequestPart("committee", [2, 3], ["id", "name"])]
        )
        result = read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {
            2: {"id": 2, "name": "Committee 2"},
            3: {"id": 3, "name": "Committee 3"},
        }

    def test_get_many_empty_part(self) -> None:
        self.write_data(self.basic_data)
        read_adapter = ReadAdapter()
        request = GetManyRequest([GetManyRequestPart("committee", [], ["id", "name"])])
        result = read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {}

    def test_get_many_multi_collection(self) -> None:
        self.write_data(self.basic_data)
        read_adapter = ReadAdapter()
        request = GetManyRequest(
            [
                GetManyRequestPart("committee", [2, 3], ["id", "name"]),
                GetManyRequestPart("theme", [1], ["accent_500"]),
                GetManyRequestPart("user", [4], ["username"]),
            ]
        )
        result = read_adapter.get_many(request)
        assert len(result) == 3
        assert result["committee"] == {
            2: {"id": 2, "name": "Committee 2"},
            3: {"id": 3, "name": "Committee 3"},
        }
        assert result["theme"] == {
            1: {"id": 1, "accent_500": "#0000ff"},
        }
        assert result["user"] == {
            4: {"id": 4, "username": "alice"},
        }

    def test_get_many_complex(self) -> None:
        self.write_data(self.basic_data)
        read_adapter = ReadAdapter()
        request = GetManyRequest(
            [
                GetManyRequestPart("committee", [2, 3], ["name"]),
                GetManyRequestPart("committee", [1, 3, 4], ["description"]),
            ]
        )
        result = read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {
            1: {"id": 1, "description": "a"},
            2: {"id": 2, "name": "Committee 2"},
            3: {"id": 3, "name": "Committee 3", "description": "c"},
            4: {"id": 4},
        }

    def test_get_many_two_parts_same_fields(self) -> None:
        self.write_data(self.basic_data)
        read_adapter = ReadAdapter()
        request = GetManyRequest(
            [
                GetManyRequestPart("committee", [2, 3], ["name"]),
                GetManyRequestPart("committee", [1, 3, 4], ["name"]),
            ]
        )
        result = read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {
            1: {"id": 1, "name": "Committee 1"},
            2: {"id": 2, "name": "Committee 2"},
            3: {"id": 3, "name": "Committee 3"},
            4: {"id": 4, "name": "Committee 4"},
        }

    def test_get_many_all_fields(self) -> None:
        self.write_data(self.basic_data)
        read_adapter = ReadAdapter()
        request = GetManyRequest(
            [
                GetManyRequestPart("committee", [2, 3], []),
                GetManyRequestPart("committee", [1, 3, 4], ["description"]),
            ]
        )
        result = read_adapter.get_many(request)
        assert len(result) == 1
        assert result["committee"] == {
            1: {"id": 1, "description": "a"},
            2: {
                "id": 2,
                "name": "Committee 2",
                "description": "b",
                "organization_id": 1,
            },
            3: {
                "id": 3,
                "name": "Committee 3",
                "description": "c",
                "organization_id": 1,
            },
            4: {"id": 4},
        }

    def test_get_many_wrong_format(self) -> None:
        with self.assertRaises(
            Exception, msg="Fqfield-based get_many request not supported"
        ):
            self.write_data(self.basic_data)
            read_adapter = ReadAdapter()
            request = GetManyRequest(["committee/2/id"])
            read_adapter.get_many(request)
