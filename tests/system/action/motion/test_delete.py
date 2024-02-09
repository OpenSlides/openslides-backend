from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "motion_ids": [111, 112],
                "is_active_in_organization_id": 1,
                "meeting_user_ids": [5],
            },
            "user/1": {"meeting_user_ids": [5]},
            "motion/111": {
                "title": "title_srtgb123",
                "meeting_id": 1,
                "state_id": 78,
                "submitter_ids": [12],
            },
            "motion/112": {
                "title": "title_fgehemn",
                "meeting_id": 1,
                "state_id": 78,
            },
            "motion_state/78": {
                "meeting_id": 1,
                "allow_submitter_edit": True,
                "motion_ids": [111, 112],
            },
            "motion_submitter/12": {
                "meeting_id": 1,
                "motion_id": 111,
                "meeting_user_id": 5,
            },
            "meeting_user/5": {
                "meeting_id": 1,
                "user_id": 1,
                "motion_submitter_ids": [12],
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

    def test_delete_with_forwardings_all_origin_ids(self) -> None:
        self.set_models(
            {
                "meeting/1": {"motion_ids": [110], "is_active_in_organization_id": 1},
                "meeting/2": {"motion_ids": [111], "is_active_in_organization_id": 1},
                "motion/110": {
                    "meeting_id": 1,
                    "derived_motion_ids": [111],
                    "all_derived_motion_ids": [111],
                },
                "motion/111": {
                    "meeting_id": 2,
                    "origin_id": 110,
                    "all_origin_ids": [110],
                },
            }
        )
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/111", ["Motion deleted"])
        self.assert_history_information("motion/110", ["Forwarded motion deleted"])

    def test_delete_with_forwardings_all_derived_motion_ids(self) -> None:
        self.set_models(
            {
                "meeting/1": {"motion_ids": [110], "is_active_in_organization_id": 1},
                "meeting/2": {"motion_ids": [111], "is_active_in_organization_id": 1},
                "motion/110": {
                    "meeting_id": 1,
                    "derived_motion_ids": [111],
                    "all_derived_motion_ids": [111],
                },
                "motion/111": {
                    "meeting_id": 2,
                    "origin_id": 110,
                    "all_origin_ids": [110],
                },
            }
        )
        response = self.request("motion.delete", {"id": 110})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/110", ["Motion deleted"])
        self.assert_history_information("motion/111", ["Origin motion deleted"])

    def test_delete_with_forwardings_complex(self) -> None:
        self.set_models(
            {
                "meeting/1": {"motion_ids": [110], "is_active_in_organization_id": 1},
                "meeting/2": {"motion_ids": [111], "is_active_in_organization_id": 1},
                "motion/110": {
                    "meeting_id": 1,
                    "derived_motion_ids": [111],
                    "all_derived_motion_ids": [111, 112, 113],
                },
                "motion/111": {
                    "meeting_id": 2,
                    "origin_id": 110,
                    "all_origin_ids": [110],
                    "derived_motion_ids": [112],
                    "all_derived_motion_ids": [112, 113],
                },
                "motion/112": {
                    "meeting_id": 1,
                    "origin_id": 111,
                    "all_origin_ids": [110, 111],
                    "derived_motion_ids": [113],
                    "all_derived_motion_ids": [113],
                },
                "motion/113": {
                    "meeting_id": 2,
                    "origin_id": 112,
                    "all_origin_ids": [110, 111, 112],
                },
            }
        )
        response = self.request_multi(
            "motion.delete", [{"id": 111}, {"id": 112}, {"id": 113}]
        )
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/110", ["Forwarded motion deleted"])
        self.assert_history_information(
            "motion/111", ["Motion deleted", "Forwarded motion deleted"]
        )
        self.assert_history_information(
            "motion/112",
            ["Motion deleted", "Forwarded motion deleted", "Origin motion deleted"],
        )
        self.assert_history_information(
            "motion/113", ["Motion deleted", "Origin motion deleted"]
        )

    def test_delete_with_submodels(self) -> None:
        self.set_models(
            {
                "meeting/1": {"motion_ids": [110], "is_active_in_organization_id": 1},
                "motion/110": {
                    "meeting_id": 1,
                    "submitter_ids": [1],
                    "change_recommendation_ids": [1],
                },
                "motion_submitter/1": {
                    "meeting_id": 1,
                    "motion_id": 110,
                    "meeting_user_id": 1,
                },
                "meeting_user/1": {
                    "user_id": 1,
                    "meeting_id": 1,
                    "motion_submitter_ids": [1],
                },
                "user/1": {"meeting_user_ids": [1]},
                "motion_change_recommendation/1": {"meeting_id": 1, "motion_id": 110},
            }
        )
        response = self.request("motion.delete", {"id": 110})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/110", ["Motion deleted"])

    def test_delete_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.delete",
            {"id": 112},
        )

    def test_delete_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.delete",
            {"id": 112},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_delete_permission_submitter(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.permission_test_models["meeting_user/2"] = {
            "meeting_id": 1,
            "user_id": self.user_id,
            "motion_submitter_ids": [12],
        }
        self.permission_test_models["motion_submitter/12"]["meeting_user_id"] = 2
        self.set_models({f"user/{self.user_id}": {"meeting_user_ids": [2]}})
        self.set_models(self.permission_test_models)
        self.set_user_groups(self.user_id, [3])
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
