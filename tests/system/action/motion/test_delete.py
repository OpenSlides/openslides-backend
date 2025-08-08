from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(98)
        self.create_motion(98, 111)
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "committee/1": {"meeting_ids": [1]},
            "meeting/1": {
                "motion_ids": [111, 112],
                "is_active_in_organization_id": 1,
                "meeting_user_ids": [5],
                "committee_id": 1,
            },
            "user/1": {"meeting_user_ids": [5]},
            "motion/111": {
                "title": "title_srtgb123",
                "meeting_id": 1,
                "state_id": 78,
                "submitter_ids": [12],
                "amendment_ids": [222],
                "sequential_number": 1,
            },
            "motion/112": {
                "title": "title_fgehemn",
                "meeting_id": 1,
                "state_id": 78,
                "sequential_number": 2,
            },
            "motion/222": {
                "title": "amendment to 111",
                "meeting_id": 1,
                "state_id": 78,
                "lead_motion_id": 111,
                "sequential_number": 3,
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
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion/111")
        self.assert_history_information("motion/111", ["Motion deleted"])

    def test_delete_amendment(self) -> None:
        self.create_amendment(98, 111, 222)
        response = self.request("motion.delete", {"id": 222})
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/111")
        self.assert_model_not_exists("motion/222")
        self.assert_history_information("motion/222", ["Motion deleted"])

    def test_delete_motion_and_amendment(self) -> None:
        self.create_amendment(98, 111, 222)
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
        # Assert error message

    def test_delete_correct_cascading(self) -> None:
        self.create_amendment(98, 111, 112)
        self.set_models(
            {
                "motion/111": {"list_of_speakers_id": 222, "agenda_item_id": 333},
                "list_of_speakers/222": {
                    "closed": False,
                    "content_object_id": "motion/111",
                    "meeting_id": 98,
                    "sequential_number": 222,
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
                "projector/1": {"meeting_id": 98, "sequential_number": 1},
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

    def test_delete_with_forwardings_all_origin_ids(self) -> None:
        self.create_meeting(1)
        self.create_motion(1, 1)
        self.set_models(
            {
                "motion/1": {
                    "derived_motion_ids": [111],
                    "all_derived_motion_ids": [111],
                },
                "motion/111": {"origin_id": 1, "all_origin_ids": [1]},
            }
        )
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/111", ["Motion deleted"])
        self.assert_history_information("motion/1", ["Forwarded motion deleted"])

    def test_delete_with_forwardings_all_derived_motion_ids(self) -> None:
        self.create_meeting(1)
        self.create_motion(1, 1)
        self.set_models(
            {
                "motion/1": {
                    "derived_motion_ids": [111],
                    "all_derived_motion_ids": [111],
                },
                "motion/111": {"origin_id": 1, "all_origin_ids": [1]},
            }
        )
        response = self.request("motion.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/1", ["Motion deleted"])
        self.assert_history_information("motion/111", ["Origin motion deleted"])

    def test_delete_with_forwardings_complex(self) -> None:
        self.create_motion(98, 113)
        self.create_meeting(1)
        self.create_motion(1, 110)
        self.create_motion(1, 112)

        self.set_models(
            {
                "motion/111": {"origin_id": 110},
                "motion/112": {"origin_id": 111},
                "motion/113": {"origin_id": 112},
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

    # TODO: fix. Fails when updating history
    def test_delete_with_submodels(self) -> None:
        self.set_user_groups(1, [98])
        self.set_models(
            {
                "motion_submitter/1": {
                    "meeting_id": 98,
                    "motion_id": 111,
                    "meeting_user_id": 1,
                },
                "motion_editor/1": {
                    "meeting_id": 98,
                    "motion_id": 111,
                    "meeting_user_id": 1,
                },
                "motion_working_group_speaker/1": {
                    "meeting_id": 98,
                    "motion_id": 111,
                    "meeting_user_id": 1,
                },
                "motion_change_recommendation/1": {"meeting_id": 98, "motion_id": 111},
            }
        )
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("motion_submitter/1")
        self.assert_model_not_exists("motion_editor/1")
        self.assert_model_not_exists("motion_working_group_speaker/1")
        self.assert_history_information("motion/111", ["Motion deleted"])

    def test_delete_no_permission(self) -> None:
        self.base_permission_test({}, "motion.delete", {"id": 111})

    def test_delete_permission(self) -> None:
        self.base_permission_test(
            {
                "meeting_user/1": {
                    "meeting_id": 98,
                    "user_id": 2,
                },
                "motion_submitter/12": {
                    "meeting_id": 98,
                    "meeting_user_id": 1,
                    "motion_id": 111,
                },
                "motion_state/111": {"allow_submitter_edit": True},
            },
            "motion.delete",
            {"id": 111},
            Permissions.Motion.CAN_MANAGE,
        )
        self.assert_model_not_exists("motion/111")

    def test_delete_permission_locked_meeting(self) -> None:
        self.create_meeting(1)
        self.create_motion(1, 110)

        self.base_locked_out_superadmin_permission_test(
            {}, "motion.delete", {"id": 110}
        )
        self.assert_model_exists("motion/110")

    def test_delete_permission_submitter(self) -> None:
        self.set_organization_management_level(None)
        self.set_user_groups(1, [98])
        self.set_models(
            {
                "motion_submitter/12": {
                    "meeting_id": 98,
                    "meeting_user_id": 1,
                    "motion_id": 111,
                },
                "motion_state/111": {"allow_submitter_edit": True},
            }
        )
        response = self.request("motion.delete", {"id": 111})
        self.assert_status_code(response, 200)
