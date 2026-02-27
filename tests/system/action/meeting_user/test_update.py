from datetime import datetime
from decimal import Decimal

from tests.system.action.base import BaseActionTestCase


class MeetingUserUpdate(BaseActionTestCase):
    def test_update(self) -> None:
        self.create_meeting(10)
        self.set_models(
            {
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "structure_level/31": {"name": "structy", "meeting_id": 10},
            }
        )
        test_dict = {
            "id": 5,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
            "group_ids": [12],
        }
        response = self.request("meeting_user.update", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/5", {**test_dict, "vote_weight": Decimal("1.5")}
        )

    def test_update_merge_fields_correct(self) -> None:
        self.create_meeting()
        self.set_user_groups(1, [1])
        self.create_user("dummy", [2])
        test_dict = {
            "assignment_candidate_ids": [1],
            "motion_working_group_speaker_ids": [1],
            "motion_editor_ids": [1],
            "motion_supporter_ids": [1],
            "chat_message_ids": [1],
        }
        self.set_models(
            {
                "meeting_user/2": test_dict,
                "list_of_speakers/11": {
                    "content_object_id": "assignment/11",
                    "meeting_id": 1,
                },
                "list_of_speakers/12": {
                    "content_object_id": "motion/11",
                    "meeting_id": 1,
                },
                "assignment/11": {
                    "title": "somehow, someone",
                    "meeting_id": 1,
                },
                "assignment_candidate/1": {
                    "meeting_id": 1,
                    "assignment_id": 11,
                    "meeting_user_id": 2,
                },
                "motion/11": {
                    "title": "morse",
                    "state_id": 1,
                    "meeting_id": 1,
                },
                "motion_working_group_speaker/1": {
                    "meeting_id": 1,
                    "motion_id": 11,
                    "meeting_user_id": 2,
                },
                "motion_editor/1": {
                    "motion_id": 11,
                    "meeting_id": 1,
                    "meeting_user_id": 2,
                },
                "chat_group/1": {"name": "talk", "meeting_id": 1},
                "chat_message/1": {
                    "meeting_id": 1,
                    "chat_group_id": 1,
                    "created": datetime.now(),
                    "content": "bla",
                    "meeting_user_id": 2,
                },
                "motion_supporter/1": {
                    "motion_id": 11,
                    "meeting_id": 1,
                    "meeting_user_id": 2,
                },
            }
        )
        response = self.request(
            "meeting_user.update", {"id": 1, **test_dict}, internal=True
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", {"id": 1, **test_dict})
        self.assert_model_exists(
            "meeting_user/2",
            {
                "assignment_candidate_ids": None,
                "motion_working_group_speaker_ids": None,
                "motion_editor_ids": None,
                "motion_supporter_ids": None,
                "chat_message_ids": None,
            },
        )

    def test_update_anonymous_group_id(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4], "anonymous_group_id": 4},
                "group/4": {"name": "groupy", "meeting_id": 1},
            }
        )
        self.create_user("dummy", [1])
        response = self.request(
            "meeting_user.update",
            {
                "id": 1,
                "group_ids": [4],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot add explicit users to a meetings anonymous group",
            response.json["message"],
        )

    def test_update_checks_locked_out_with_error(self) -> None:
        self.create_meeting(10)
        self.set_models(
            {
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "group/12": {"permissions": ["user.can_manage"]},
                "structure_level/31": {"name": "structy", "meeting_id": 10},
            }
        )
        test_dict = {
            "id": 5,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
            "group_ids": [12],
            "locked_out": True,
        }
        response = self.request("meeting_user.update", test_dict)
        self.assert_status_code(response, 400)
        assert (
            "Cannot lock user from meeting 10 as long as he has the OrganizationManagementLevel superadmin"
            == response.json["message"]
        )

    def test_update_locked_out_allowed(self) -> None:
        self.create_meeting(10)
        self.set_models({"structure_level/31": {"name": "structy", "meeting_id": 10}})
        self.create_user("test", [12])
        test_dict = {
            "id": 1,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
            "group_ids": [12],
            "locked_out": True,
        }
        response = self.request("meeting_user.update", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1", {"id": 1, **test_dict, "vote_weight": Decimal("1.5")}
        )
