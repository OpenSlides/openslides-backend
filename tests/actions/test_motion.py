from unittest import TestCase

# from openslides_backend.actions import Payload
from openslides_backend.actions.motion.delete import MotionDelete

from ..fake_services.database import DatabaseTestAdapter
from ..fake_services.permission import PermissionTestAdapter

from ..utils import (  # Client,; ResponseWrapper,; create_test_application,;
    get_fqfield,
    get_fqid,
)

# from openslides_backend.shared.exceptions import ActionException, PermissionDenied


class BaseMotionDeleteActionTester(TestCase):
    """
    Tests the motion delete action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [{"id": 2995885358}]


class MotionDeleteActionUnitTester(BaseMotionDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = MotionDelete(PermissionTestAdapter(), DatabaseTestAdapter())
        self.action.user_id = (
            7826715669  # This user has perm MOTION_CAN_MANAGE for some meetings.
        )

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        self.assertEqual(dataset["position"], 1)
        self.maxDiff = None
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": {
                        "id": self.valid_payload_1[0]["id"],
                        "meeting_id": None,
                        "motion_statute_paragraph_id": None,
                        "sort_parent_id": None,
                        "parent_id": None,
                        "motion_category_id": None,
                        "motion_block_id": None,
                        "origin_id": None,
                        "state_id": None,
                        "recommendation_id": None,
                        "supporter_ids": None,
                        "mediafile_attachment_ids": None,
                        "tag_ids": None,
                    },
                    "references": {
                        get_fqfield("meeting/5562405520/motion_ids"): {
                            "type": "remove",
                            "value": [],
                        },
                        get_fqfield("motion_state/5205893377/motion_active_ids"): {
                            "type": "remove",
                            "value": [],
                        },
                        get_fqfield("motion_state/5205893377/motion_recommended_ids"): {
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
                    "cascade_delete": {},
                }
            ],
        )


class MotionDeleteActionPerformTester(BaseMotionDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = MotionDelete(PermissionTestAdapter(), DatabaseTestAdapter())
        self.user_id = (
            7826715669  # This user has perm MOTION_CAN_MANAGE for some meetings.
        )

    def test_perform_correct_1(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {"type": "delete", "fqid": get_fqid("motion/2995885358")},
                    {
                        "type": "update",
                        "fqfields": {get_fqfield("meeting/5562405520/motion_ids"): []},
                    },
                    {
                        "type": "update",
                        "fqfields": {
                            get_fqfield("motion_block/4116433002/motion_ids"): []
                        },
                    },
                    {
                        "type": "update",
                        "fqfields": {
                            get_fqfield("motion_category/8734727380/motion_ids"): []
                        },
                    },
                    {
                        "type": "update",
                        "fqfields": {
                            get_fqfield(
                                "motion_state/5205893377/motion_recommended_ids"
                            ): []
                        },
                    },
                    {
                        "type": "update",
                        "fqfields": {
                            get_fqfield("motion_state/5205893377/motion_active_ids"): []
                        },
                    },
                ],
                "information": {
                    get_fqid("motion/2995885358"): ["Object deleted"],
                    get_fqid("meeting/5562405520"): [
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
                "locked_fields": {
                    get_fqfield("motion/2995885358/deleted"): 1,
                    get_fqfield("meeting/5562405520/motion_ids"): 1,
                    get_fqfield("motion_state/5205893377/motion_active_ids"): 1,
                    get_fqfield("motion_state/5205893377/motion_recommended_ids"): 1,
                    get_fqfield("motion_category/8734727380/motion_ids"): 1,
                    get_fqfield("motion_block/4116433002/motion_ids"): 1,
                },
            },
        ]
        self.maxDiff = None
        self.assertEqual(
            list(write_request_elements), expected,
        )


# 8264607531
# 4740630442
# 3265963568
# 2279328478
# 1082050467
# 8000824551
# 7268025091
# 2704380002
# 5265142974
# 4173926977
# 2792847341
# 5411457713
# 3878502438
# 2833375327
# pheK0Ja3ai ohXa5Joo2e ohcae9AhTa eiQua7iem1 ahPheiG8fu zu0oaBeeba
# ilieJa3fou iph3ia9Ahr voh1zeid1Y aa0Aok4the eib8Ne6aif beek5Veexu Cheexi4see
# vaeb1AiPei HohN8googa Pha7Dei7oe Re2Aazei0O agh8eiM4ul paX6aigeem
