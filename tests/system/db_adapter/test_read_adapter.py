from datastore.reader.core.requests import GetManyRequest, GetManyRequestPart

from openslides_backend.services.datastore.read_adapter import ReadAdapter
from .base_relational_db_test import BaseRelationalDBTestCase

class TestReadAdapter(BaseRelationalDBTestCase):
    def test_get_many(self) -> None:
        # TODO: This probably writes the wrong data format.
        self.write_data(
            [
                {
                    "table": "organizationT",
                    "fields": ["id", "name", "default_language", "theme_id"],
                    "rows": [(1, "Orga 1", "en", 1)],
                },
                {
                    "table": "themeT",
                    "fields": ["id", "name", "accent_500", "primary_500", "warn_500"],
                    "rows": [(1, "Theme 1", 255, 256 * 255, 256 * 256 * 255)],
                },
                {
                    "table": "committeeT",
                    "fields": ["id", "name"],
                    "rows": [
                        (1, "Committee 1"),
                        (2, "Committee 2"),
                        (3, "Committee 3"),
                    ],
                },
            ]
        )
        read_adapter = ReadAdapter()
        request = GetManyRequest([GetManyRequestPart("committee", [2, 3], ["id", "name"])])
        result = read_adapter.get_many(request)
        assert result["committee"] == {
            2: {"id": 2, "name": "Committee 2"},
            3: {"id": 3, "name": "Committee 3"},
        }
