from copy import deepcopy
from typing import Any, Dict, List, Sequence

from openslides_backend.services.datastore.interface import (
    Aggregate,
    Count,
    Found,
    GetManyRequest,
    PartialModel,
)
from openslides_backend.shared.filters import Filter, FilterOperator
from openslides_backend.shared.interfaces import WriteRequestElement
from openslides_backend.shared.patterns import Collection, FullQualifiedId

# Do not change order of this entries. Just append new ones.
TESTDATA = [
    {
        "collection": "mediafile",
        "id": 3549387598,
        "fields": {
            "meeting_ids": [3611987967],
            "attachment_ids": [
                FullQualifiedId(collection=Collection("topic"), id=6259289755)
            ],
        },
    },
    {
        "collection": "mediafile",
        "id": 7583920032,
        "fields": {"meeting_ids": [], "attachment_ids": []},
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
            "attachment_ids": [3549387598],
        },
    },
    {
        "collection": "meeting",
        "id": 7816466305,
        "fields": {"committee_id": 5914213969, "topic_ids": [1312354708]},
    },
    {
        "collection": "organisation",
        "id": 1,
        "fields": {"committee_ids": [5914213969, 7826715669]},
    },
    {
        "collection": "committee",
        "id": 5914213969,
        "fields": {"organisation_id": 1, "meeting_ids": [7816466305, 3908439961]},
    },
    {
        "collection": "meeting",
        "id": 3908439961,
        "fields": {"committee_id": 5914213969, "topic_ids": []},
    },
    # Motion test:
    {"collection": "user", "id": 7268025091, "fields": {}},
    {
        "collection": "committee",
        "id": 7826715669,
        "fields": {"organisation_id": 1, "meeting_ids": [5562405520]},
    },
    {
        "collection": "meeting",
        "id": 5562405520,
        "fields": {"committee_id": 7826715669, "motion_ids": [2995885358]},
    },
    {
        "collection": "motion",
        "id": 2995885358,
        "fields": {
            "title": "title_ruZ9nu3yee",
            "meeting_id": 5562405520,
            "state_id": 5205893377,
            "recommendation_id": 5205893377,
            "category_id": 8734727380,
            "block_id": 4116433002,
            "statute_paragraph_id": 8264607531,
        },
    },
    {
        "collection": "motion_state",
        "id": 5205893377,
        "fields": {
            "meeting_id": 5562405520,
            "motion_ids": [2995885358],
            "motion_recommendation_ids": [2995885358],
        },
    },
    {
        "collection": "motion_category",
        "id": 8734727380,
        "fields": {"meeting_id": 5562405520, "motion_ids": [2995885358]},
    },
    {
        "collection": "motion_block",
        "id": 4116433002,
        "fields": {"meeting_id": 5562405520, "motion_ids": [2995885358]},
    },
    {
        "collection": "motion_block",
        "id": 4740630442,
        "fields": {"meeting_id": 5562405520, "motion_ids": []},
    },
    {
        "collection": "motion_statute_paragraph",
        "id": 8264607531,
        "fields": {"meeting_id": 5562405520, "motion_ids": [2995885358]},
    },
    # Sort motions (not fully related)
    {
        "collection": "motion",
        "id": 3265963568,
        "fields": {"meeting_id": 5562405520, "sort_child_ids": []},
    },
    {
        "collection": "motion",
        "id": 2279328478,
        "fields": {"meeting_id": 5562405520, "sort_child_ids": []},
    },
    {
        "collection": "motion",
        "id": 1082050467,
        "fields": {"meeting_id": 5562405520, "sort_child_ids": [8000824551]},
    },
    {
        "collection": "motion",
        "id": 8000824551,
        "fields": {"meeting_id": 5562405520, "sort_parent_id": 1082050467},
    },
    # Agenda test:
    {
        "collection": "meeting",
        "id": 9079236097,
        "fields": {
            "topic_ids": [5756367535],
            "agenda_item_ids": [3393211712],
            "user_ids": [5968705978],
        },
    },
    {
        "collection": "topic",
        "id": 5756367535,
        "fields": {"meeting_id": 9079236097, "agenda_item_id": 3393211712},
    },
    {
        "collection": "agenda_item",
        "id": 3393211712,
        "fields": {"meeting_id": 9079236097, "content_object_id": "topic/5756367535"},
    },
]  # type: List[Dict[str, Any]]


class DatabaseTestAdapter:
    """
    Test adapter for database (read) queries.

    See openslides_backend.adapters.protocols.DatabaseProvider for
    implementation.
    """

    position = 1

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> PartialModel:
        get_many_request = GetManyRequest(fqid.collection, [fqid.id], mapped_fields)
        result = self.get_many([get_many_request])
        return result[fqid.collection][fqid.id]

    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        if mapped_fields is not None:
            raise NotImplementedError(
                "This test adapter does not support this field yet."
            )
        result = {}
        for get_many_request in get_many_requests:
            inner_result = {}
            for data in deepcopy(TESTDATA):
                if (
                    data["collection"] == str(get_many_request.collection)
                    and data["id"] in get_many_request.ids
                ):
                    element = {}
                    if get_many_request.mapped_fields is None:
                        element = data["fields"]
                    else:
                        for field in get_many_request.mapped_fields:
                            if field in data["fields"].keys():
                                element[field] = data["fields"][field]
                    inner_result[data["id"]] = element
            if len(get_many_request.ids) != len(inner_result):
                # Something was not found.
                print(get_many_request, inner_result)
                raise RuntimeError
            result[get_many_request.collection] = inner_result
        return result

    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str] = None,
        get_deleted_models: int = None,
    ) -> List[PartialModel]:
        raise NotImplementedError

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
    ) -> List[PartialModel]:
        result = []
        for data in deepcopy(TESTDATA):
            data_meeting_id = data["fields"].get("meeting_id")
            if meeting_id is not None and (
                data_meeting_id is None or data_meeting_id != meeting_id
            ):
                continue
            if data["collection"] != str(collection):
                continue
            if not isinstance(filter, FilterOperator):
                raise NotImplementedError
            if filter.operator == "==":
                if data["fields"].get(filter.field) == filter.value:
                    element = {}
                    if mapped_fields is None:
                        element = data["fields"]
                        element["id"] = data["id"]
                    else:
                        for field in mapped_fields:
                            if field in data["fields"].keys():
                                element[field] = data["fields"][field]
                            if field == "id":
                                element["id"] = data["id"]
                    result.append(element)
            else:
                raise NotImplementedError
        return result

    def exists(self, collection: Collection, filter: Filter) -> Found:
        raise NotImplementedError

    def count(self, collection: Collection, filter: Filter) -> Count:
        raise NotImplementedError

    def min(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        raise NotImplementedError

    def max(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        raise NotImplementedError

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        raise NotImplementedError("This test method is not implemented.")

    def reserve_id(self, collection: Collection) -> int:
        return 42

    def write(self, write_requests: Sequence[WriteRequestElement]) -> None:
        pass
