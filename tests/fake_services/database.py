from copy import deepcopy
from typing import Any, Dict, List, Tuple

from openslides_backend.shared.filters import Filter, FilterOperator
from openslides_backend.shared.patterns import Collection, FullQualifiedId

# Do not change order of this entries. Just append new ones.
TESTDATA = [
    {
        "collection": "mediafile_attachment",
        "id": 3549387598,
        "fields": {"meeting_ids": [3611987967], "topic_ids": [6259289755]},
    },
    {
        "collection": "mediafile_attachment",
        "id": 7583920032,
        "fields": {"meeting_ids": [], "topic_ids": []},
    },
    {
        "collection": "topic",
        "id": 1312354708,
        "fields": {"meeting_id": 7816466305, "title": "title_Aevoozu3ua"},
    },
    {
        "collection": "mediafile_pubilc_file",
        "id": 9283748294,
        "fields": {"meeting_id": 4256427454},
    },
    {
        "collection": "meeting",
        "id": 2393342057,
        "fields": {"topic_ids": [], "user_ids": [5968705978, 4796568680]},
    },
    {
        "collection": "meeting",
        "id": 4002059810,
        "fields": {"topic_ids": [], "user_ids": [5968705978]},
    },
    {
        "collection": "meeting",
        "id": 3611987967,
        "fields": {"topic_ids": [6375863023, 6259289755], "user_ids": [5968705978]},
        "mediafile_attachment_ids": [3549387598],
    },
    {
        "collection": "topic",
        "id": 6375863023,
        "fields": {"meeting_id": 3611987967, "title": "title_ahpout2aFa"},
    },
    {
        "collection": "topic",
        "id": 6259289755,
        "fields": {
            "meeting_id": 3611987967,
            "title": "title_ub0eeYushu",
            "mediafile_attachment_ids": [3549387598],
        },
    },
    {
        "collection": "meeting",
        "id": 7816466305,
        "fields": {"committee_id": 5914213969, "topic_ids": [1312354708]},
    },
    {"collection": "organisation", "id": 1, "fields": {"committee_ids": [5914213969]}},
    {
        "collection": "committee",
        "id": 5914213969,
        "fields": {"organisation_id": 1, "meeting_ids": [7816466305]},
    },
]  # type: List[Dict[str, Any]]


class DatabaseTestAdapter:
    """
    Test adapter for database (read) queries.

    See openslides_backend.adapters.protocols.DatabaseProvider for
    implementation.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def get(
        self, fqid: FullQualifiedId, mapped_fields: List[str] = None
    ) -> Tuple[Dict[str, Any], int]:
        result, position = self.getMany(fqid.collection, [fqid.id], mapped_fields)
        return result[fqid.id], position

    def getMany(
        self, collection: Collection, ids: List[int], mapped_fields: List[str] = None
    ) -> Tuple[Dict[int, Dict[str, Any]], int]:
        result = {}
        for data in deepcopy(TESTDATA):
            if data["collection"] == str(collection) and data["id"] in ids:
                element = {}
                if mapped_fields is None:
                    element = data["fields"]
                else:
                    for field in mapped_fields:
                        if field in data["fields"].keys():
                            element[field] = data["fields"][field]
                result[data["id"]] = element
        if len(ids) != len(result):
            # Something was not found.
            raise RuntimeError
        return (result, 1)

    def getId(self, collection: Collection) -> Tuple[int, int]:
        return (42, 1)

    def exists(self, collection: Collection, ids: List[int]) -> Tuple[bool, int]:
        for id in ids:
            for data in TESTDATA:
                if data["id"] == id:
                    break
            else:
                return (False, 1)
        return (True, 1)

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
    ) -> Tuple[Dict[int, Dict[str, Any]], int]:
        result = {}
        for data in deepcopy(TESTDATA):
            data_meeting_id = data["fields"].get("meeting_id")
            if meeting_id is not None and (
                data_meeting_id is None or data_meeting_id != meeting_id
            ):
                continue
            if data["collection"] != str(collection):
                continue
            if not isinstance(filter, FilterOperator):
                # TODO: Implement other filters
                continue
            if (
                filter.operator == "=="
                and data["fields"].get(filter.field) == filter.value
            ):
                element = {}
                if mapped_fields is None:
                    element = data["fields"]
                else:
                    for field in mapped_fields:
                        if field in data["fields"].keys():
                            element[field] = data["fields"][field]
                result[data["id"]] = element
                continue
            # TODO: Implement other operators.
        return (result, 1)
