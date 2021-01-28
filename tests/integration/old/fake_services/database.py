from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Sequence

from openslides_backend.services.datastore.interface import (
    Count,
    Found,
    GetManyRequest,
    OptionalInt,
    PartialModel,
)
from openslides_backend.shared.filters import Filter, FilterOperator
from openslides_backend.shared.interfaces import WriteRequest
from openslides_backend.shared.patterns import Collection, FullQualifiedId

TEST_POSITION = 1

OLD_TESTDATA = {
    "mediafile_pubilc_file": {9283748294: {"meeting_id": 4256427454}},
    "mediafile": {
        3549387598: {
            "meeting_ids": [3611987967],
            "attachment_ids": ["topic/6259289755"],
        },
        7583920032: {"meeting_ids": [], "attachment_ids": []},
    },
    "agenda_item": {
        3393211712: {"meeting_id": 9079236097, "content_object_id": "topic/5756367535"},
    },
    "topic": {
        1312354708: {"meeting_id": 7816466305, "title": "title_Aevoozu3ua"},
        6375863023: {"meeting_id": 3611987967, "title": "title_ahpout2aFa"},
        6259289755: {
            "meeting_id": 3611987967,
            "title": "title_ub0eeYushu",
            "attachment_ids": [3549387598],
        },
        5756367535: {"meeting_id": 9079236097, "agenda_item_id": 3393211712},
    },
    "meeting": {
        2393342057: {"topic_ids": [], "user_ids": [5968705978, 4796568680]},
        4002059810: {"topic_ids": [], "user_ids": [5968705978]},
        3611987967: {"topic_ids": [6375863023, 6259289755], "user_ids": [5968705978]},
        7816466305: {"committee_id": 5914213969, "topic_ids": [1312354708]},
        3908439961: {"committee_id": 5914213969, "topic_ids": []},
        5562405520: {"committee_id": 7826715669, "motion_ids": [2995885358]},
        9079236097: {
            "topic_ids": [5756367535],
            "agenda_item_ids": [3393211712],
            "user_ids": [5968705978],
        },
    },
    "organisation": {1: {"committee_ids": [5914213969, 7826715669]}},
    "committee": {
        5914213969: {"organisation_id": 1, "meeting_ids": [7816466305, 3908439961]},
        7826715669: {"organisation_id": 1, "meeting_ids": [5562405520]},
    },
    # Motion test:
    "user": {7268025091: {}},
    "motion": {
        2995885358: {
            "title": "title_ruZ9nu3yee",
            "meeting_id": 5562405520,
            "state_id": 5205893377,
            "recommendation_id": 5205893377,
            "category_id": 8734727380,
            "block_id": 4116433002,
            "statute_paragraph_id": 8264607531,
        },
        3265963568: {"meeting_id": 5562405520, "sort_child_ids": []},
        2279328478: {"meeting_id": 5562405520, "sort_child_ids": []},
        1082050467: {"meeting_id": 5562405520, "sort_child_ids": [8000824551]},
        8000824551: {"meeting_id": 5562405520, "sort_parent_id": 1082050467},
    },
    "motion_state": {
        5205893377: {
            "meeting_id": 5562405520,
            "motion_ids": [2995885358],
            "motion_recommendation_ids": [2995885358],
        },
    },
    "motion_category": {
        8734727380: {"meeting_id": 5562405520, "motion_ids": [2995885358]},
    },
    "motion_block": {
        4116433002: {"meeting_id": 5562405520, "motion_ids": [2995885358]},
        4740630442: {"meeting_id": 5562405520, "motion_ids": []},
    },
    "motion_statute_paragraph": {
        8264607531: {"meeting_id": 5562405520, "motion_ids": [2995885358]},
    },
}  # type: Dict[str, Dict[int, Dict[str, Any]]]


class DatastoreTestAdapter:
    """
    Test adapter for datastore (read) queries.
    See openslides_backend.adapters.interface.Datastore for implementation.
    """

    # The key of this dictionary is a stringified FullQualifiedId or FullQualifiedField
    locked_fields: Dict[str, int]
    # TODO: This adapter does not set locked_fields so you can't use it here. Fix this.

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.initial_data: Dict[str, Dict[int, Dict[str, Any]]]
        datastore_content = kwargs.get("datastore_content")
        if datastore_content is not None:
            self.initial_data = defaultdict(lambda: defaultdict(dict))
            for fqfield, value in datastore_content.items():
                self.initial_data[str(fqfield.collection)][fqfield.id][
                    fqfield.field
                ] = value
        else:
            if not kwargs.get("old_style_testing"):
                raise ValueError(
                    "DatastoreTestAdapter should be used with datastore_content or with old_style_testing set to True."
                )
            self.initial_data = deepcopy(OLD_TESTDATA)

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
        lock_result: bool = False,
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
        lock_result: bool = False,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        if mapped_fields is not None:
            raise NotImplementedError(
                "This test adapter does not support this field yet."
            )
        if position is not None:
            raise NotImplementedError("This keyword is not supported at the moment.")
        if get_deleted_models is not None:
            raise NotImplementedError("This keyword is not supported at the moment.")
        result = {}
        for get_many_request in get_many_requests:
            inner_result = {}
            for instance_id in get_many_request.ids:
                data = self.initial_data.get(str(get_many_request.collection), {}).get(
                    instance_id, {}
                )
                element = {}
                if get_many_request.mapped_fields is None:
                    element = data
                    if lock_result:
                        element["meta_position"] = TEST_POSITION
                else:
                    for field in get_many_request.mapped_fields:
                        if field in data.keys():
                            element[field] = data[field]
                        elif field == "meta_position":
                            element["meta_position"] = TEST_POSITION
                    if lock_result:
                        element.setdefault("meta_position", TEST_POSITION)
                inner_result[instance_id] = element
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
        lock_result: bool = False,
    ) -> Dict[int, PartialModel]:
        raise NotImplementedError

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str] = None,
        lock_result: bool = False,
    ) -> Dict[int, PartialModel]:
        result = {}
        for instance_id, data in self.initial_data.get(str(collection), {}).items():
            if not isinstance(filter, FilterOperator):
                raise NotImplementedError
            if filter.operator == "=":
                if data.get(filter.field) == filter.value:
                    element = {}
                    if mapped_fields is None:
                        element = data
                        element["id"] = instance_id
                        if lock_result:
                            element["meta_position"] = TEST_POSITION
                    else:
                        for field in mapped_fields:
                            if field in data.keys():
                                element[field] = data[field]
                            elif field == "id":
                                element["id"] = instance_id
                            elif field == "meta_position":
                                element["meta_position"] = TEST_POSITION
                        if lock_result:
                            element.setdefault("id", instance_id)
                            element.setdefault("meta_position", TEST_POSITION)
                    result[instance_id] = element
            else:
                raise NotImplementedError
        return result

    def exists(
        self, collection: Collection, filter: Filter, lock_result: bool = False
    ) -> Found:
        raise NotImplementedError

    def count(
        self, collection: Collection, filter: Filter, lock_result: bool = False
    ) -> Count:
        raise NotImplementedError

    def min(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> OptionalInt:
        raise NotImplementedError

    def max(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> OptionalInt:
        raise NotImplementedError

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        raise NotImplementedError("This test method is not implemented.")

    def reserve_id(self, collection: Collection) -> int:
        return 42

    def write(self, write_request: WriteRequest) -> None:
        pass

    def truncate_db(self) -> None:
        pass
