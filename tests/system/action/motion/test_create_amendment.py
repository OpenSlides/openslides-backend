from typing import Any

from psycopg.types.json import Jsonb

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase
from tests.util import Response


class MotionCreateAmendmentActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1)
        self.set_models(
            {
                "motion_category/12": {
                    "meeting_id": 1,
                    "name": "Category 12",
                    "sequential_number": 1,
                },
                "motion_block/13": {
                    "meeting_id": 1,
                    "title": "Block 13",
                    "sequential_number": 1,
                },
            }
        )
        self.default_action_data = {
            "title": "test_Xcdfgee",
            "meeting_id": 1,
            "lead_motion_id": 1,
            "text": "text_test1",
        }

    def test_create_amendment(self) -> None:
        response = self.request(
            "motion.create",
            {
                **self.default_action_data,
                "block_id": 13,
                "category_id": 12,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {
                **self.default_action_data,
                "block_id": 13,
                "category_id": 12,
            },
        )

    def test_create_amendment_inherited_category(self) -> None:
        self.set_models({"motion/1": {"category_id": 12, "block_id": 13}})
        response = self.request(
            "motion.create",
            self.default_action_data,
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"block_id": None, "category_id": 12})

    def test_create_amendment_default_workflow(self) -> None:
        response = self.request(
            "motion.create",
            self.default_action_data,
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {
                **self.default_action_data,
                "state_id": 1,
            },
        )

    def create_with_amendment_paragraphs(self, amendment_paragraphs: Any) -> Response:
        return self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "lead_motion_id": 1,
                "amendment_paragraphs": amendment_paragraphs,
            },
        )

    def test_create_with_amendment_paragraphs_valid(self) -> None:
        response = self.create_with_amendment_paragraphs({4: "text"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"amendment_paragraphs": {"4": "text"}})

    def test_create_with_amendment_paragraphs_0(self) -> None:
        response = self.create_with_amendment_paragraphs({0: "text"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"amendment_paragraphs": {"0": "text"}})

    def test_create_with_amendment_paragraphs_string(self) -> None:
        response = self.create_with_amendment_paragraphs({"0": "text"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"amendment_paragraphs": {"0": "text"}})

    def test_create_with_amendment_paragraphs_letter_in_key(self) -> None:
        response = self.create_with_amendment_paragraphs({"a4": "text"})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion.create: data.amendment_paragraphs must not contain {'a4'} properties",
            response.json["message"],
        )

    def test_create_with_amendment_paragraphs_array(self) -> None:
        response = self.create_with_amendment_paragraphs(["test"])
        self.assert_status_code(response, 400)
        self.assertEqual(
            "data.amendment_paragraphs must be object", response.json["message"]
        )

    def test_create_with_amendment_paragraphs_html(self) -> None:
        response = self.create_with_amendment_paragraphs(
            {
                "0": "<it>test</it>",
                "1": "</><</>broken>",
            }
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {
                "amendment_paragraphs": {
                    "0": "&lt;it&gt;test&lt;/it&gt;",
                    "1": "&lt;broken&gt;",
                }
            },
        )

    def test_create_missing_text(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        assert "Text or amendment_paragraphs is required in this context." in str(
            response.json["message"]
        )

    def test_create_text_and_amendment_paragraphs(self) -> None:
        response = self.request(
            "motion.create",
            {
                **self.default_action_data,
                "amendment_paragraphs": {4: "text"},
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "You can't give both of text and amendment_paragraphs",
            response.json["message"],
        )

    def test_create_missing_reason(self) -> None:
        self.set_models({"meeting/1": {"motions_reason_required": True}})
        response = self.request(
            "motion.create",
            self.default_action_data,
        )
        self.assert_status_code(response, 400)
        self.assertEqual("Reason is required", response.json["message"])

    def test_create_identical_amendment(self) -> None:
        text = "test"
        hash = TextHashMixin.get_hash(text)
        self.create_motion(
            meeting_id=1,
            base=2,
            motion_data={"lead_motion_id": 1, "text": text, "text_hash": hash},
        )
        response = self.request(
            "motion.create",
            {
                "title": "test",
                "meeting_id": 1,
                "lead_motion_id": 1,
                "text": text,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/3", {"text_hash": hash, "identical_motion_ids": [2]}
        )

    def test_create_identical_amendment_for_other_motion(self) -> None:
        text = "test"
        hash = TextHashMixin.get_hash(text)
        self.create_motion(meeting_id=1, base=2)
        self.create_motion(
            meeting_id=1,
            base=2,
            motion_data={"lead_motion_id": 2, "text": text, "text_hash": hash},
        )
        response = self.request(
            "motion.create",
            {
                "title": "test",
                "meeting_id": 1,
                "lead_motion_id": 1,
                "text": text,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/3", {"text_hash": hash, "identical_motion_ids": None}
        )

    def test_create_identical_paragraph_based_amendment(self) -> None:
        paragraphs = {1: "test"}
        amendment = {
            "title": "Amendment 1",
            "lead_motion_id": 1,
            "amendment_paragraphs": paragraphs,
        }
        hash = TextHashMixin.get_hash_for_motion(amendment)
        amendment.update({"text_hash": hash, "amendment_paragraphs": Jsonb(paragraphs)})
        self.create_motion(1, 2, motion_data=amendment)
        response = self.request(
            "motion.create",
            {
                "title": "test",
                "meeting_id": 1,
                "lead_motion_id": 1,
                "amendment_paragraphs": paragraphs,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/3", {"text_hash": hash, "identical_motion_ids": [2]}
        )

    def setup_permissions(self, permissions: list[Permission]) -> None:
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(
            3,
            permissions,
        )

    def test_create_amendment_permission(self) -> None:
        self.setup_permissions(
            [Permissions.Motion.CAN_CREATE, Permissions.Motion.CAN_CREATE_AMENDMENTS]
        )
        response = self.request(
            "motion.create",
            self.default_action_data,
        )
        self.assert_status_code(response, 200)

    def test_create_amendment_no_permission(self) -> None:
        self.setup_permissions([Permissions.Motion.CAN_CREATE])
        response = self.request(
            "motion.create",
            self.default_action_data,
        )
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action motion.create. Missing Permission: motion.can_create_amendments",
            response.json["message"],
        )

    def test_create_amendment_non_admin(self) -> None:
        self.setup_permissions(
            [
                Permissions.Motion.CAN_CREATE,
                Permissions.Motion.CAN_CREATE_AMENDMENTS,
                Permissions.Motion.CAN_MANAGE,
            ],
        )
        self.set_models({"motion/1": {"category_id": 12, "block_id": 13}})
        response = self.request(
            "motion.create",
            {
                **self.default_action_data,
                "category_id": 12,
                "block_id": 13,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"block_id": 13, "category_id": 12})

    def test_create_amendment_no_permissions_extra_fields(self) -> None:
        self.setup_permissions(
            [Permissions.Motion.CAN_CREATE, Permissions.Motion.CAN_CREATE_AMENDMENTS]
        )
        for field in ("block_id", "category_id"):
            response = self.request(
                "motion.create",
                {
                    **self.default_action_data,
                    field: 12,
                },
            )
            self.assert_status_code(response, 403)
            self.assertEqual("Forbidden fields: {field}", response.json["message"])
