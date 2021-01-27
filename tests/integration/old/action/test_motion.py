import time
from copy import deepcopy
from typing import Any, Dict

from openslides_backend.action.motion.delete import MotionDelete
from openslides_backend.action.motion.sort import MotionSort
from openslides_backend.action.motion.update import MotionUpdate, MotionUpdateMetadata
from openslides_backend.shared.exceptions import ActionException, PermissionDenied
from tests.system.action.base import BaseActionTestCase
from tests.util import Client, get_fqfield, get_fqid

from ..fake_services.datastore import DatastoreTestAdapter
from ..fake_services.permission import PermissionTestAdapter
from ..util import create_test_application_old as create_test_application

# TODO: These tests use all old style datastore testing.
# Fix this (do not use create_test_applicaton_old and do not use old_style_testing=True any more).


class BaseMotionUpdateActionTester(BaseActionTestCase):
    """
    Tests the motion update action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [
            {
                "id": 2995885358,
                "title": "title_pheK0Ja3ai",
                "statute_paragraph_id": None,
            }
        ]


class MotionUpdateActionUnitTester(BaseMotionUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        user_id = 7826715669
        self.action = MotionUpdate(
            PermissionTestAdapter(superuser=user_id),
            DatastoreTestAdapter(old_style_testing=True),
        )
        self.action.user_id = user_id

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        instance = deepcopy(self.valid_payload_1[0])
        instance["last_modified"] = round(time.time())
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": instance,
                    "relations": {
                        get_fqfield("motion_statute_paragraph/8264607531/motion_ids"): {
                            "type": "remove",
                            "value": [],
                        }
                    },
                }
            ],
        )


class MotionUpdateActionPerformTester(BaseMotionUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 7826715669
        self.action = MotionUpdate(
            PermissionTestAdapter(superuser=self.user_id),
            DatastoreTestAdapter(old_style_testing=True),
        )

    def test_perform_correct_1(self) -> None:
        write_requests = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/2995885358"),
                        "fields": {
                            "title": "title_pheK0Ja3ai",
                            "last_modified": round(time.time()),
                            "statute_paragraph_id": None,
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("motion_statute_paragraph/8264607531"),
                        "fields": {"motion_ids": []},
                    },
                ],
                "information": {
                    get_fqid("motion/2995885358"): ["Object updated"],
                    get_fqid("motion_statute_paragraph/8264607531"): [
                        "Object attachment to motion reset"
                    ],
                },
                "user_id": self.user_id,
            },
        ]
        self.assertEqual(list(write_requests), expected)


class MotionUpdateActionWSGITester(BaseMotionUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 7826715669
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionView", superuser=self.user_id
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application)
        response = client.post(
            "/",
            json=[{"action": "motion.update", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 200)


class BaseMotionUpdateMetadataActionTester(BaseActionTestCase):
    """
    Tests the motion update medadata action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [
            {"id": 2995885358, "category_id": None, "block_id": 4740630442}
        ]
        self.valid_payload_2 = [{"id": 2995885358, "supporter_ids": [7268025091]}]


class MotionUpdateMetadataActionUnitTester(BaseMotionUpdateMetadataActionTester):
    def setUp(self) -> None:
        super().setUp()
        user_id = 7826715669
        self.action = MotionUpdateMetadata(
            PermissionTestAdapter(superuser=user_id),
            DatastoreTestAdapter(old_style_testing=True),
        )
        self.action.user_id = user_id

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_validation_correct_2(self) -> None:
        self.action.validate(self.valid_payload_2)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        instance = deepcopy(self.valid_payload_1[0])
        instance["last_modified"] = round(time.time())
        expected = [
            {
                "instance": instance,
                "relations": {
                    get_fqfield("motion_category/8734727380/motion_ids"): {
                        "type": "remove",
                        "value": [],
                    },
                    get_fqfield("motion_block/4116433002/motion_ids"): {
                        "type": "remove",
                        "value": [],
                    },
                    get_fqfield("motion_block/4740630442/motion_ids"): {
                        "type": "add",
                        "value": [2995885358],
                    },
                },
            }
        ]
        self.assertEqual(dataset["data"], expected)

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        instance = deepcopy(self.valid_payload_2[0])
        instance["last_modified"] = round(time.time())
        expected = [
            {
                "instance": instance,
                "relations": {
                    get_fqfield("user/7268025091/supported_motion_5562405520_ids"): {
                        "type": "add",
                        "value": [2995885358],
                    },
                },
            }
        ]
        self.assertEqual(dataset["data"], expected)


class MotionUpdateMetadataActionPerformTester(BaseMotionUpdateMetadataActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 7826715669
        self.action = MotionUpdateMetadata(
            PermissionTestAdapter(superuser=self.user_id),
            DatastoreTestAdapter(old_style_testing=True),
        )

    def test_perform_correct_1(self) -> None:
        write_requests = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/2995885358"),
                        "fields": {
                            "last_modified": round(time.time()),
                            "category_id": None,
                            "block_id": 4740630442,
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("motion_block/4116433002"),
                        "fields": {"motion_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("motion_block/4740630442"),
                        "fields": {"motion_ids": [2995885358]},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("motion_category/8734727380"),
                        "fields": {"motion_ids": []},
                    },
                ],
                "information": {
                    get_fqid("motion/2995885358"): ["Object updated"],
                    get_fqid("motion_block/4116433002"): [
                        "Object attachment to motion reset"
                    ],
                    get_fqid("motion_block/4740630442"): ["Object attached to motion"],
                    get_fqid("motion_category/8734727380"): [
                        "Object attachment to motion reset"
                    ],
                },
                "user_id": self.user_id,
            },
        ]
        self.assertEqual(
            list(write_requests),
            expected,
        )

    def test_perform_correct_2(self) -> None:
        write_requests = self.action.perform(
            self.valid_payload_2, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/2995885358"),
                        "fields": {
                            "last_modified": round(time.time()),
                            "supporter_ids": [7268025091],
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("user/7268025091"),
                        "fields": {"supported_motion_5562405520_ids": [2995885358]},
                    },
                ],
                "information": {
                    get_fqid("motion/2995885358"): ["Object updated"],
                    get_fqid("user/7268025091"): ["Object attached to motion"],
                },
                "user_id": self.user_id,
            }
        ]
        self.assertEqual(
            list(write_requests),
            expected,
        )

    def test_perform_no_permission_1(self) -> None:
        with self.assertRaises(PermissionDenied) as context_manager:
            self.action.perform(self.valid_payload_1, user_id=4796568680)
        self.assertEqual(
            context_manager.exception.message,
            "You are not allowed to perform action motion.update_metadata.",
        )


class BaseMotionDeleteActionTester(BaseActionTestCase):
    """
    Tests the motion delete action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [{"id": 2995885358}]


class MotionDeleteActionUnitTester(BaseMotionDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        user_id = 7826715669
        self.action = MotionDelete(
            PermissionTestAdapter(superuser=user_id),
            DatastoreTestAdapter(old_style_testing=True),
        )
        self.action.user_id = user_id

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        expected = [
            {
                "instance": {
                    "id": self.valid_payload_1[0]["id"],
                    "meeting_id": None,
                    "statute_paragraph_id": None,
                    "sort_parent_id": None,
                    "lead_motion_id": None,
                    "category_id": None,
                    "change_recommendation_ids": None,
                    "current_projector_ids": None,
                    "comment_ids": None,
                    "block_id": None,
                    "origin_id": None,
                    "state_id": None,
                    "recommendation_id": None,
                    "personal_note_ids": None,
                    "poll_ids": None,
                    "projection_ids": None,
                    "recommendation_extension_reference_ids": None,
                    "referenced_in_motion_recommendation_extension_ids": None,
                    "submitter_ids": None,
                    "attachment_ids": None,
                    "tag_ids": None,
                    "amendment_ids": None,
                    "derived_motion_ids": None,
                    "sort_child_ids": None,
                    "agenda_item_id": None,
                    "list_of_speakers_id": None,
                },
                "relations": {
                    get_fqfield("meeting/5562405520/motion_ids"): {
                        "type": "remove",
                        "value": [],
                    },
                    get_fqfield("motion_statute_paragraph/8264607531/motion_ids"): {
                        "type": "remove",
                        "value": [],
                    },
                    get_fqfield("motion_state/5205893377/motion_ids"): {
                        "type": "remove",
                        "value": [],
                    },
                    get_fqfield("motion_state/5205893377/motion_recommendation_ids"): {
                        "type": "remove",
                        "value": [],
                    },
                    get_fqfield("motion_category/8734727380/motion_ids"): {
                        "type": "remove",
                        "value": [],
                    },
                    get_fqfield("motion_block/4116433002/motion_ids"): {
                        "type": "remove",
                        "value": [],
                    },
                },
            }
        ]
        self.maxDiff = None
        self.assertEqual(dataset["data"], expected)


class MotionDeleteActionPerformTester(BaseMotionDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 7826715669
        self.action = MotionDelete(
            PermissionTestAdapter(superuser=self.user_id),
            DatastoreTestAdapter(old_style_testing=True),
        )

    def test_perform_correct_1(self) -> None:
        write_requests = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {"type": "delete", "fqid": get_fqid("motion/2995885358")},
                    {
                        "type": "update",
                        "fqid": get_fqid("motion_block/4116433002"),
                        "fields": {"motion_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("motion_category/8734727380"),
                        "fields": {"motion_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/5562405520"),
                        "fields": {"motion_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("motion_state/5205893377"),
                        "fields": {"motion_recommendation_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("motion_state/5205893377"),
                        "fields": {"motion_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("motion_statute_paragraph/8264607531"),
                        "fields": {"motion_ids": []},
                    },
                ],
                "information": {
                    get_fqid("motion/2995885358"): ["Object deleted"],
                    get_fqid("meeting/5562405520"): [
                        "Object attachment to motion reset"
                    ],
                    get_fqid("motion_statute_paragraph/8264607531"): [
                        "Object attachment to motion reset"
                    ],
                    get_fqid("motion_state/5205893377"): [
                        "Object attachment to motion reset",
                        "Object attachment to motion reset",
                    ],
                    get_fqid("motion_category/8734727380"): [
                        "Object attachment to motion reset"
                    ],
                    get_fqid("motion_block/4116433002"): [
                        "Object attachment to motion reset"
                    ],
                },
                "user_id": self.user_id,
            },
        ]
        self.assertEqual(
            list(write_requests),
            expected,
        )


class MotionDeleteActionWSGITester(BaseMotionDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 7826715669
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionView", superuser=self.user_id
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application)
        response = client.post(
            "/",
            json=[{"action": "motion.delete", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 200)


class BaseMotionSortActionTester(BaseActionTestCase):
    """
    Tests the motion sort action.
    """

    def setUp(self) -> None:
        self.meeting_id = 5562405520
        self.valid_payload_1 = {
            "meeting_id": self.meeting_id,
            "nodes": [
                {"id": 3265963568},
                {"id": 2279328478},
                {"id": 1082050467},
                {"id": 8000824551},
                {"id": 2995885358},
            ],
        }
        self.valid_payload_2 = {
            "meeting_id": self.meeting_id,
            "nodes": [
                {
                    "id": 3265963568,
                    "children": [
                        {
                            "id": 2279328478,
                            "children": [{"id": 8000824551}, {"id": 1082050467}],
                        }
                    ],
                },
                {"id": 2995885358},
            ],
        }
        self.circular_payload = {
            "meeting_id": self.meeting_id,
            "nodes": [
                {
                    "id": 3265963568,
                    "children": [{"id": 2279328478, "children": [{"id": 3265963568}]}],
                },
            ],
        }


class MotionSortActionUnitTester(BaseMotionSortActionTester):
    def setUp(self) -> None:
        super().setUp()
        user_id = 7826715669
        self.action = MotionSort(
            PermissionTestAdapter(superuser=user_id),
            DatastoreTestAdapter(old_style_testing=True),
        )
        self.action.user_id = user_id

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_validation_correct_2(self) -> None:
        self.action.validate(self.valid_payload_2)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        expected: Dict[int, Dict[str, Any]] = {
            3265963568: {
                "sort_parent_id": None,
                "sort_weight": 2,
                "sort_children_ids": [],
            },
            2279328478: {
                "sort_parent_id": None,
                "sort_weight": 4,
                "sort_children_ids": [],
            },
            1082050467: {
                "sort_parent_id": None,
                "sort_weight": 6,
                "sort_children_ids": [],
            },
            8000824551: {
                "sort_parent_id": None,
                "sort_weight": 8,
                "sort_children_ids": [],
            },
            2995885358: {
                "sort_parent_id": None,
                "sort_weight": 10,
                "sort_children_ids": [],
            },
        }
        self.assertEqual(dataset["data"], expected)

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        expected = {
            3265963568: {
                "sort_parent_id": None,
                "sort_weight": 2,
                "sort_children_ids": [2279328478],
            },
            2279328478: {
                "sort_parent_id": 3265963568,
                "sort_weight": 4,
                "sort_children_ids": [8000824551, 1082050467],
            },
            1082050467: {
                "sort_parent_id": 2279328478,
                "sort_weight": 8,
                "sort_children_ids": [],
            },
            8000824551: {
                "sort_parent_id": 2279328478,
                "sort_weight": 6,
                "sort_children_ids": [],
            },
            2995885358: {
                "sort_parent_id": None,
                "sort_weight": 10,
                "sort_children_ids": [],
            },
        }
        self.assertEqual(dataset["data"], expected)

    def test_circular_dataset(self) -> None:
        with self.assertRaises(ActionException) as context_manager:
            self.action.prepare_dataset(self.circular_payload)
        self.assertEqual(
            context_manager.exception.message, "Duplicate id in sort tree: 3265963568"
        )


class MotionSortActionPerformTester(BaseMotionSortActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 7826715669
        self.action = MotionSort(
            PermissionTestAdapter(superuser=self.user_id),
            DatastoreTestAdapter(old_style_testing=True),
        )

    def test_perform_correct_1(self) -> None:
        write_requests = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/3265963568"),
                        "fields": {
                            "sort_parent_id": None,
                            "sort_children_ids": [],
                            "sort_weight": 2,
                        },
                    }
                ],
                "information": {get_fqid("motion/3265963568"): ["Object sorted"]},
                "user_id": self.user_id,
            },
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/2279328478"),
                        "fields": {
                            "sort_parent_id": None,
                            "sort_weight": 4,
                            "sort_children_ids": [],
                        },
                    }
                ],
                "information": {get_fqid("motion/2279328478"): ["Object sorted"]},
                "user_id": self.user_id,
            },
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/1082050467"),
                        "fields": {
                            "sort_weight": 6,
                            "sort_parent_id": None,
                            "sort_children_ids": [],
                        },
                    }
                ],
                "information": {get_fqid("motion/1082050467"): ["Object sorted"]},
                "user_id": self.user_id,
            },
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/8000824551"),
                        "fields": {
                            "sort_parent_id": None,
                            "sort_weight": 8,
                            "sort_children_ids": [],
                        },
                    }
                ],
                "information": {get_fqid("motion/8000824551"): ["Object sorted"]},
                "user_id": self.user_id,
            },
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/2995885358"),
                        "fields": {
                            "sort_parent_id": None,
                            "sort_weight": 10,
                            "sort_children_ids": [],
                        },
                    }
                ],
                "information": {get_fqid("motion/2995885358"): ["Object sorted"]},
                "user_id": self.user_id,
            },
        ]
        self.assertEqual(
            list(write_requests),
            expected,
        )

    def test_perform_correct_2(self) -> None:
        write_requests = self.action.perform(
            self.valid_payload_2, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/3265963568"),
                        "fields": {
                            "sort_parent_id": None,
                            "sort_children_ids": [2279328478],
                            "sort_weight": 2,
                        },
                    }
                ],
                "information": {get_fqid("motion/3265963568"): ["Object sorted"]},
                "user_id": self.user_id,
            },
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/2279328478"),
                        "fields": {
                            "sort_parent_id": 3265963568,
                            "sort_weight": 4,
                            "sort_children_ids": [8000824551, 1082050467],
                        },
                    }
                ],
                "information": {get_fqid("motion/2279328478"): ["Object sorted"]},
                "user_id": self.user_id,
            },
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/8000824551"),
                        "fields": {
                            "sort_parent_id": 2279328478,
                            "sort_weight": 6,
                            "sort_children_ids": [],
                        },
                    }
                ],
                "information": {get_fqid("motion/8000824551"): ["Object sorted"]},
                "user_id": self.user_id,
            },
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/1082050467"),
                        "fields": {
                            "sort_weight": 8,
                            "sort_parent_id": 2279328478,
                            "sort_children_ids": [],
                        },
                    }
                ],
                "information": {get_fqid("motion/1082050467"): ["Object sorted"]},
                "user_id": self.user_id,
            },
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("motion/2995885358"),
                        "fields": {
                            "sort_parent_id": None,
                            "sort_weight": 10,
                            "sort_children_ids": [],
                        },
                    }
                ],
                "information": {get_fqid("motion/2995885358"): ["Object sorted"]},
                "user_id": self.user_id,
            },
        ]
        self.assertEqual(
            list(write_requests),
            expected,
        )


class MotionSortActionWSGITester(BaseMotionSortActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 7826715669
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionView", superuser=self.user_id
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application)
        response = client.post(
            "/",
            json=[{"action": "motion.sort", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 200)
