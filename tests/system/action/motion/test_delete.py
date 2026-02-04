from typing import Any

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from tests.system.action.base import BaseActionTestCase


class BaseMotionDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1)
        self.create_motion(1, 111)


class MotionDeleteActionTest(BaseMotionDeleteActionTest):
    def create_amendment(
        self,
        meeting_id: int,
        base: int,
        lead_motion_id: int,
        motion_data: dict[str, Any] = {},
    ) -> None:
        self.create_motion(
            meeting_id,
            base,
            motion_data={"lead_motion_id": lead_motion_id, **motion_data},
        )

    def test_delete_correct(self) -> None:
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"history_position_ids": [1]})
        self.assert_model_not_exists("motion/111")
        self.assert_model_exists(
            "history_position/1",
            {"original_user_id": 1, "user_id": 1, "entry_ids": [1]},
        )
        self.assert_model_exists(
            "history_entry/1",
            {
                "entries": ["Motion deleted"],
                "original_model_id": "motion/111",
                "model_id": None,
                "position_id": 1,
            },
        )
        self.assert_history_information("motion/111", ["Motion deleted"])

    def test_delete_amendment(self) -> None:
        self.create_amendment(1, 222, 111)
        response = self.request("motion.delete", {"id": 222})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/111")
        self.assert_model_not_exists("motion/222")
        self.assert_history_information("motion/222", ["Motion deleted"])

    def test_delete_motion_and_amendment(self) -> None:
        self.create_amendment(1, 222, 111)
        response = self.request_multi("motion.delete", [{"id": 111}, {"id": 222}])
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion/111")
        self.assert_model_not_exists("motion/222")
        self.assert_history_information("motion/111", ["Motion deleted"])
        self.assert_history_information("motion/222", ["Motion deleted"])

    def test_delete_wrong_id(self) -> None:
        response = self.request("motion.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion/111")
        self.assertEqual("Model 'motion/112' does not exist.", response.json["message"])

    def test_delete_correct_cascading(self) -> None:
        self.create_amendment(meeting_id=1, base=112, lead_motion_id=111)
        self.set_models(
            {
                "agenda_item/333": {
                    "comment": "test_comment_ewoirzewoirioewr",
                    "content_object_id": "motion/111",
                    "meeting_id": 1,
                },
                "projection/1": {
                    "content_object_id": "motion/111",
                    "current_projector_id": 1,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion/111")
        self.assert_model_not_exists("agenda_item/333")
        self.assert_model_not_exists("list_of_speakers/222")
        self.assert_model_not_exists("projection/1")
        self.assert_model_not_exists("motion/112")
        self.assert_model_exists("projector/1", {"current_projection_ids": None})

    def set_forwarded_motion(
        self,
        meeting_id: int = 4,
        base: int = 112,
        origin_id: int = 111,
        all_origin_ids: list[int] = [111],
    ) -> None:
        self.create_motion(meeting_id, base, motion_data={"origin_id": origin_id})
        for id_ in all_origin_ids:
            self.update_model(
                fqid_from_collection_and_id("motion", id_),
                {},
                {"add": {"all_derived_motion_ids": [base]}},
            )

    def test_delete_with_forwardings_all_origin_ids(self) -> None:
        self.create_meeting(4)
        self.set_forwarded_motion()
        response = self.request("motion.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/112", ["Motion deleted"])
        self.assert_history_information("motion/111", ["Forwarded motion deleted"])

    def test_delete_with_forwardings_all_derived_motion_ids(self) -> None:
        self.create_meeting(4)
        self.set_forwarded_motion()
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/111", ["Motion deleted"])
        self.assert_history_information("motion/112", ["Origin motion deleted"])

    def test_delete_with_forwardings_complex(self) -> None:
        self.create_meeting(4)
        self.set_forwarded_motion(4, 112, 111)
        self.set_forwarded_motion(1, 113, 112, [111, 112])
        self.set_forwarded_motion(4, 114, 113, [111, 112, 113])

        response = self.request_multi(
            "motion.delete", [{"id": 112}, {"id": 113}, {"id": 114}]
        )
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/111", ["Forwarded motion deleted"])
        self.assert_history_information(
            "motion/112", ["Motion deleted", "Forwarded motion deleted"]
        )
        self.assert_history_information(
            "motion/113",
            ["Motion deleted", "Forwarded motion deleted", "Origin motion deleted"],
        )
        self.assert_history_information(
            "motion/114", ["Motion deleted", "Origin motion deleted"]
        )

    def test_delete_with_submodels(self) -> None:
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "motion_submitter/1": {
                    "meeting_id": 1,
                    "motion_id": 111,
                    "meeting_user_id": 1,
                },
                "motion_editor/1": {
                    "meeting_id": 1,
                    "motion_id": 111,
                    "meeting_user_id": 1,
                },
                "motion_working_group_speaker/1": {
                    "meeting_id": 1,
                    "motion_id": 111,
                    "meeting_user_id": 1,
                },
                "motion_change_recommendation/1": {"meeting_id": 1, "motion_id": 111},
            }
        )
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_submitter/1")
        self.assert_model_not_exists("motion_editor/1")
        self.assert_model_not_exists("motion_working_group_speaker/1")
        self.assert_history_information("motion/111", ["Motion deleted"])


class MotionDeletePermissionTest(BaseMotionDeleteActionTest):
    def setUp(self) -> None:
        super().setUp()
        self.create_motion(1, 112)
        self.create_motion(1, 222, motion_data={"lead_motion_id": 111})
        self.permission_test_models: dict[str, Any] = {
            "motion_submitter/12": {
                "meeting_user_id": 5,
                "motion_id": 111,
                "meeting_id": 1,
            },
            "meeting_user/5": {"user_id": 2, "meeting_id": 1},
            "motion_state/1": {"allow_submitter_edit": True},
        }

    def test_delete_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models, "motion.delete", {"id": 112}
        )
        self.assert_model_exists("motion/112")

    def test_delete_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )
        self.assert_model_not_exists("motion/111")

    def test_delete_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models, "motion.delete", {"id": 112}
        )
        self.assert_model_exists("motion/112")

    def test_delete_permission_submitter(self) -> None:
        self.base_permission_test(
            self.permission_test_models, "motion.delete", {"id": 111}, fail=False
        )
        self.assert_model_not_exists("motion/111")
