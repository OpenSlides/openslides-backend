from typing import Any, Dict, Iterable, cast

from openslides_backend.action.actions.meeting.shared_meeting import (
    meeting_projector_default_object_list,
)
from tests.system.action.base import BaseActionTestCase


class MeetingCreateActionTest(BaseActionTestCase):
    def basic_test(self, datapart: Dict[str, Any]) -> Dict[str, Any]:
        self.create_model("committee/1", {"name": "test_committee", "member_ids": [2]})
        self.create_model("group/1")
        self.create_model("user/2")

        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
                "welcome_title": "test_wel_title",
                **datapart,
            },
        )
        self.assert_status_code(response, 200)
        return self.get_model("meeting/1")

    def test_create_simple(self) -> None:
        meeting = self.basic_test(dict())
        self.assertCountEqual(
            cast(Iterable[Any], meeting.get("default_projector_$_id")),
            meeting_projector_default_object_list,
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "name": "test_name",
                "committee_id": 1,
                "group_ids": [2, 3, 4, 5, 6],
                "default_group_id": 2,
                "admin_group_id": 3,
                "motion_workflow_ids": [1],
                "motions_default_workflow_id": 1,
                "motions_default_amendment_workflow_id": 1,
                "motions_default_statute_amendment_workflow_id": 1,
                "motion_state_ids": [1, 2, 3, 4],
                "user_ids": [1],
            },
        )
        self.assert_model_exists("group/2", {"name": "Default"})
        self.assert_model_exists("group/3", {"name": "Admin", "user_ids": [1]})
        self.assert_model_exists("group/4", {"name": "Delegates"})
        self.assert_model_exists("group/5", {"name": "Staff"})
        self.assert_model_exists("group/6", {"name": "Committees"})
        self.assert_model_exists(
            "motion_workflow/1",
            {
                "name": "Simple Workflow",
                "meeting_id": 1,
                "default_workflow_meeting_id": 1,
                "default_amendment_workflow_meeting_id": 1,
                "default_statute_amendment_workflow_meeting_id": 1,
                "state_ids": [1, 2, 3, 4],
                "first_state_id": 1,
            },
        )
        self.assert_model_exists(
            "motion_state/1", {"name": "submitted", "next_state_ids": [2, 3, 4]}
        )
        self.assert_model_exists(
            "motion_state/2",
            {
                "name": "accepted",
                "previous_state_ids": [1],
                "meeting_id": 1,
                "workflow_id": 1,
            },
        )
        self.assert_model_exists(
            "motion_state/3", {"name": "rejected", "previous_state_ids": [1]}
        )
        self.assert_model_exists(
            "motion_state/4", {"name": "not_decided", "previous_state_ids": [1]}
        )
        projector1 = self.get_model("projector/1")
        self.assertCountEqual(
            cast(Iterable[Any], projector1.get("used_as_default_$_in_meeting_id")),
            meeting_projector_default_object_list,
        )
        self.assert_model_exists(
            "projector/1",
            {
                "name": "Default projector",
                "meeting_id": 1,
                "used_as_reference_projector_meeting_id": 1,
            }.update(
                {
                    f"used_as_default_${name}_in_meeting_id": 1
                    for name in meeting_projector_default_object_list
                }
            ),
        )
        self.assert_model_exists(
            "user/1",
            {
                "group_$1_ids": [3],  # meeting/1 and group 3
                "group_$_ids": ["1"],  # only meeting/1 values
            },
        )

    def test_check_action_data_fields(self) -> None:
        meeting = self.basic_test(
            {
                "welcome_text": "htXiSgbj",
                "description": "RRfnzxHA",
                "location": "LSFHPTgE",
                "start_time": 1608120653,
                "end_time": 1608121653,
                "url_name": "JWdYZqDX",
                "enable_anonymous": False,
                "guest_ids": [2],
            }
        )
        assert meeting.get("welcome_text") == "htXiSgbj"
        assert meeting.get("description") == "RRfnzxHA"
        assert meeting.get("location") == "LSFHPTgE"
        assert meeting.get("start_time") == 1608120653
        assert meeting.get("end_time") == 1608121653
        assert meeting.get("url_name") == "JWdYZqDX"
        assert meeting.get("enable_anonymous") is False
        assert meeting.get("guest_ids") == [2]
        assert meeting.get("user_ids") == [1, 2]
        user_2 = self.get_model("user/2")
        assert user_2.get("guest_meeting_ids") == [1]

    def test_guest_ids_error(self) -> None:
        self.create_model("committee/1", {"name": "test_committee", "member_ids": [2]})
        self.create_model("user/2")
        self.create_model("user/3")

        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
                "welcome_title": "test_wel_title",
                "guest_ids": [2, 3],
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "Guest-ids {3} are not part of committee-member or manager_ids.",
            response.json["message"],
        )
