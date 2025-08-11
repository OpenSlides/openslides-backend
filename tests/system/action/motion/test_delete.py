from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1)
        self.create_motion(1, 111)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/112": {
                "title": "title_fgehemn",
                "meeting_id": 1,
                "state_id": 111,
                "sequential_number": 112,
            },
            "motion/222": {
                "title": "amendment to 111",
                "meeting_id": 1,
                "state_id": 111,
                "lead_motion_id": 111,
                "sequential_number": 222,
            },
            "motion_state/111": {"allow_submitter_edit": True},
            "motion_submitter/12": {
                "meeting_id": 1,
                "motion_id": 111,
                "meeting_user_id": 5,
            },
            "meeting_user/5": {
                "meeting_id": 1,
                "user_id": 2,
                "motion_submitter_ids": [12],
            },
        }

    def create_amendment(
        self, meeting_id: int, lead_motion_id: int, base: int = 2
    ) -> None:
        self.create_motion(meeting_id, base)
        self.set_models({f"motion/{base}": {"lead_motion_id": lead_motion_id}})

    def test_delete_correct(self) -> None:
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion/111")
        self.assert_history_information("motion/111", ["Motion deleted"])

    def test_delete_amendment(self) -> None:
        self.create_amendment(1, 111, 222)
        response = self.request("motion.delete", {"id": 222})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/111")
        self.assert_model_not_exists("motion/222")
        self.assert_history_information("motion/222", ["Motion deleted"])

    def test_delete_motion_and_amendment(self) -> None:
        self.create_amendment(1, 111, 222)
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
        self.create_amendment(1, 111, 112)
        self.set_models(
            {
                "motion/111": {"list_of_speakers_id": 222, "agenda_item_id": 333},
                "list_of_speakers/222": {
                    "closed": False,
                    "content_object_id": "motion/111",
                    "meeting_id": 1,
                    "sequential_number": 222,
                },
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

    def set_forwarded_motion(self) -> None:
        self.create_meeting(4)
        self.create_motion(4, 112)
        self.set_models({"motion/112": {"origin_id": 111, "all_origin_ids": [111]}})

    def test_delete_with_forwardings_all_origin_ids(self) -> None:
        self.set_forwarded_motion()
        response = self.request("motion.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/112", ["Motion deleted"])
        self.assert_history_information("motion/111", ["Forwarded motion deleted"])

    def test_delete_with_forwardings_all_derived_motion_ids(self) -> None:
        self.set_forwarded_motion()
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/111", ["Motion deleted"])
        self.assert_history_information("motion/112", ["Origin motion deleted"])

    def test_delete_with_forwardings_complex(self) -> None:
        self.create_motion(1, 113)
        self.create_meeting(4)
        self.create_motion(4, 112)
        self.create_motion(4, 114)

        self.set_models(
            {
                "motion/112": {"origin_id": 111},
                "motion/113": {"origin_id": 112},
                "motion/114": {"origin_id": 113},
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
