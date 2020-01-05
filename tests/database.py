from typing import Any, Dict, List, Tuple

from openslides_backend.utils.types import Collection, FullQualifiedId

# Do not change order of this entries. Just append new ones.
TESTDATA = [
    {
        "collection": "mediafile_attachment",
        "id": 3549387598,
        "fields": {"topic_ids": []},
    },
    {
        "collection": "mediafile_attachment",
        "id": 7583920032,
        "fields": {"topic_ids": []},
    },
    {"collection": "topic", "id": 1312354708, "fields": {"title": "title_Aevoozu3ua"}},
    {"collection": "mediafile_pubilc_file", "id": 9283748294, "fields": {}},
]  # type: List[Dict[str, Any]]


class DatabaseTestAdapter:
    """
    Test adapter for database (read) queries.

    See openslides_backend.services.providers.DatabaseProvider for
    implementation.
    """

    def __init__(*args: Any, **kwargs: Any) -> None:
        pass

    def get(self, fqid: FullQualifiedId, mapped_fields: List[str] = None) -> None:
        ...

    def getMany(
        self, collection: Collection, ids: List[int], mapped_fields: List[str] = None
    ) -> Tuple[Dict[int, Dict[str, Any]], int]:
        result = {}
        for data in TESTDATA:
            if data["collection"] == str(collection) and data["id"] in ids:
                element = {}
                if mapped_fields:
                    for field in mapped_fields:
                        if field in data["fields"].keys():
                            element[field] = data["fields"][field]
                result[data["id"]] = element
        if len(ids) != len(result):
            raise RuntimeError
        return (result, 1)

    def getId(self, collection: Collection) -> Tuple[int, int]:
        return (42, 1)
