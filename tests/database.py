from typing import Any, Dict, List, Tuple

from openslides_backend.utils.types import Collection, FullQualifiedId

# Do not change order of this entries. Just append new ones.
TESTDATA = [
    {
        "collection": "mediafile.attachment",
        "id": 3549387598,
        "fields": {"topic_ids": []},
    },
    {
        "collection": "mediafile.attachment",
        "id": 7583920032,
        "fields": {"topic_ids": []},
    },
    {"collection": "topic", "id": 1312354708, "fields": {"title": "title_Aevoozu3ua"}},
    {"collection": "mediafile.pubilc_file", "id": 9283748294, "fields": {}},
]  # type: List[Dict[str, Any]]


class DatabaseTestAdapter:
    def get(self, fqid: FullQualifiedId, mapped_fields: List[str] = None) -> None:
        ...

    def getMany(
        self, collection: Collection, ids: List[int], mapped_fields: List[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        result = []
        for data in TESTDATA:
            if data["collection"] == str(collection) and data["id"] in ids:
                element = {"id": data["id"]}
                if mapped_fields:
                    for field in mapped_fields:
                        if field in data["fields"].keys():
                            element[field] = data["fields"][field]
                result.append(element)
        return (result, 1)

    def getId(self, collection: Collection) -> Tuple[int, int]:
        return (42, 1)
