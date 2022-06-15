from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: Dict[str, Dict[str, Any]] = {
            "meeting/1": {"motion_ids": [111], "is_active_in_organization_id": 1},
            "motion/111": {
                "title": "title_srtgb123",
                "meeting_id": 1,
                "state_id": 78,
                "submitter_ids": [12],
            },
            "motion_state/78": {
                "meeting_id": 1,
                "allow_submitter_edit": True,
                "motion_ids": [111],
            },
            "motion_submitter/12": {
                "meeting_id": 1,
                "motion_id": 111,
                "user_id": 1,
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/98": {"motion_ids": [111], "is_active_in_organization_id": 1},
                "motion/111": {"title": "title_srtgb123", "meeting_id": 98},
            }
        )
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion/111")
        self.assert_history_information("motion/111", ["Motion deleted"])

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion/112", {"title": "title_srtgb123"})
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion/112")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "meeting/98": {
                    "motion_ids": [111],
                    "all_projection_ids": [1],
                    "is_active_in_organization_id": 1,
                },
                "motion/111": {
                    "title": "title_srtgb123",
                    "list_of_speakers_id": 222,
                    "agenda_item_id": 333,
                    "projection_ids": [1],
                    "meeting_id": 98,
                },
                "list_of_speakers/222": {
                    "closed": False,
                    "content_object_id": "motion/111",
                    "meeting_id": 98,
                },
                "agenda_item/333": {
                    "comment": "test_comment_ewoirzewoirioewr",
                    "content_object_id": "motion/111",
                    "meeting_id": 98,
                },
                "projection/1": {
                    "content_object_id": "motion/111",
                    "current_projector_id": 1,
                    "meeting_id": 98,
                },
                "projector/1": {
                    "current_projection_ids": [1],
                    "meeting_id": 98,
                },
            }
        )
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion/111")
        self.assert_model_deleted("agenda_item/333")
        self.assert_model_deleted("list_of_speakers/222")
        self.assert_model_deleted("projection/1")
        self.assert_model_exists("projector/1", {"current_projection_ids": []})

    def test_delete_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.delete",
            {"id": 111},
        )

    def test_delete_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_delete_permission_submitter(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.permission_test_models["motion_submitter/12"]["user_id"] = self.user_id
        self.set_models(self.permission_test_models)
        self.set_user_groups(self.user_id, [3])
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
