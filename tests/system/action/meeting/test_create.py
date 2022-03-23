from typing import Any, Dict, Iterable, List, cast

from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from tests.system.action.base import BaseActionTestCase


class MeetingCreateActionTest(BaseActionTestCase):
    def basic_test(self, datapart: Dict[str, Any]) -> Dict[str, Any]:
        self.set_models(
            {
                "organization/1": {"limit_of_meetings": 0, "active_meeting_ids": []},
                "committee/1": {
                    "name": "test_committee",
                    "user_ids": [2],
                    "organization_id": 1,
                },
                "group/1": {},
                "user/2": {},
                "organization_tag/3": {},
            }
        )

        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
                "organization_tag_ids": [3],
                **datapart,
            },
        )
        self.assert_status_code(response, 200)
        return self.get_model("meeting/1")

    def test_create_simple_and_complex_workflow(self) -> None:
        meeting = self.basic_test(dict())
        self.assertCountEqual(
            cast(Iterable[Any], meeting.get("default_projector_$_id")),
            cast(List[str], Meeting.default_projector__id.replacement_enum),
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "name": "test_name",
                "committee_id": 1,
                "group_ids": [2, 3, 4, 5, 6],
                "default_group_id": 2,
                "admin_group_id": 3,
                "motion_workflow_ids": [1, 2],
                "motions_default_workflow_id": 1,
                "motions_default_amendment_workflow_id": 1,
                "motions_default_statute_amendment_workflow_id": 1,
                "motion_state_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                "list_of_speakers_countdown_id": 1,
                "poll_countdown_id": 2,
                "projector_countdown_warning_time": 0,
                "organization_tag_ids": [3],
                "is_active_in_organization_id": 1,
                "assignment_poll_default_group_ids": [4],
                "motion_poll_default_group_ids": [4],
                **{
                    f"default_projector_${name}_id": 1
                    for name in cast(
                        List[str], Meeting.default_projector__id.replacement_enum
                    )
                },
            },
        )
        self.assert_model_exists("organization/1", {"active_meeting_ids": [1]})
        self.assert_model_exists("group/2", {"name": "Default"})
        self.assert_model_exists("group/3", {"name": "Admin"})
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
            "motion_state/4", {"name": "not decided", "previous_state_ids": [1]}
        )
        self.assert_model_exists(
            "motion_workflow/2",
            {
                "name": "Complex Workflow",
                "meeting_id": 1,
                "state_ids": [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                "first_state_id": 5,
            },
        )
        self.assert_model_exists(
            "motion_state/5", {"name": "in progress", "next_state_ids": [6, 10]}
        )
        self.assert_model_exists(
            "motion_state/6", {"name": "submitted", "previous_state_ids": [5]}
        )
        self.assert_model_exists(
            "motion_state/7", {"name": "permitted", "previous_state_ids": [6]}
        )
        self.assert_model_exists(
            "motion_state/8", {"name": "accepted", "previous_state_ids": [7]}
        )
        self.assert_model_exists(
            "motion_state/9", {"name": "rejected", "previous_state_ids": [7]}
        )
        self.assert_model_exists(
            "motion_state/10", {"name": "withdrawn", "previous_state_ids": [5, 6, 7]}
        )
        self.assert_model_exists(
            "motion_state/11", {"name": "adjourned", "previous_state_ids": [7]}
        )
        self.assert_model_exists(
            "motion_state/12", {"name": "not concerned", "previous_state_ids": [7]}
        )
        self.assert_model_exists(
            "motion_state/13",
            {"name": "referred to committee", "previous_state_ids": [7]},
        )
        self.assert_model_exists(
            "motion_state/14", {"name": "needs review", "previous_state_ids": [7]}
        )
        self.assert_model_exists(
            "motion_state/15",
            {"name": "rejected (not authorized)", "previous_state_ids": [6]},
        )
        projector1 = self.get_model("projector/1")
        self.assertCountEqual(
            cast(Iterable[Any], projector1.get("used_as_default_$_in_meeting_id")),
            cast(List[str], Meeting.default_projector__id.replacement_enum),
        )
        self.assert_model_exists(
            "projector/1",
            {
                "name": "Default projector",
                "meeting_id": 1,
                "used_as_reference_projector_meeting_id": 1,
                **{
                    f"used_as_default_${name}_in_meeting_id": 1
                    for name in cast(
                        List[str], Meeting.default_projector__id.replacement_enum
                    )
                },
            },
        )
        self.assert_model_exists(
            "projector_countdown/1",
            {
                "title": "List of speakers countdown",
                "meeting_id": 1,
                "used_as_list_of_speakers_countdown_meeting_id": 1,
                "default_time": 60,
                "countdown_time": 60,
            },
        )
        self.assert_model_exists(
            "projector_countdown/2",
            {
                "title": "Voting countdown",
                "meeting_id": 1,
                "used_as_poll_countdown_meeting_id": 1,
                "default_time": 60,
                "countdown_time": 60,
            },
        )

    def test_check_action_data_fields(self) -> None:
        meeting = self.basic_test(
            {
                "description": "RRfnzxHA",
                "location": "LSFHPTgE",
                "start_time": 1608120653,
                "end_time": 1608121653,
            }
        )
        assert meeting.get("description") == "RRfnzxHA"
        assert meeting.get("location") == "LSFHPTgE"
        assert meeting.get("start_time") == 1608120653
        assert meeting.get("end_time") == 1608121653

        # check two defaults:
        assert meeting.get("assignment_poll_default_type") == "pseudoanonymous"
        assert meeting.get("assignment_poll_default_method") == "Y"

    def test_create_check_users(self) -> None:
        meeting = self.basic_test({"user_ids": [2]})
        assert meeting.get("user_ids") == [2]
        default_group_id = meeting.get("default_group_id")
        self.assert_model_exists(
            "user/2", {f"group_${meeting['id']}_ids": [default_group_id]}
        )

    def test_create_check_admins(self) -> None:
        meeting = self.basic_test({"admin_ids": [2]})
        assert meeting.get("user_ids") == [2]
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists(
            "user/2", {f"group_${meeting['id']}_ids": [admin_group_id]}
        )

    def test_create_with_same_user_in_users_and_admins(self) -> None:
        meeting = self.basic_test({"user_ids": [2], "admin_ids": [2]})
        assert meeting.get("user_ids") == [2]
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists(
            "user/2", {f"group_${meeting['id']}_ids": [admin_group_id]}
        )

    def test_create_multiple_users(self) -> None:
        self.set_models(
            {
                "organization/1": {"limit_of_meetings": 0, "active_meeting_ids": []},
                "committee/1": {"organization_id": 1},
                "user/2": {},
                "user/3": {},
            }
        )
        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
                "user_ids": [2, 3],
                "admin_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        default_group_id = meeting.get("default_group_id")
        self.assert_model_exists(
            "user/2", {"group_$1_ids": [default_group_id], "committee_ids": [1]}
        )
        self.assert_model_exists(
            "user/3", {"group_$1_ids": [default_group_id], "committee_ids": [1]}
        )
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists(
            "user/1", {"group_$1_ids": [admin_group_id], "committee_ids": [1]}
        )
        self.assertCountEqual(meeting.get("user_ids"), [1, 2, 3])
        committee = self.get_model("committee/1")
        self.assertCountEqual(committee.get("user_ids"), [1, 2, 3])

    def test_create_with_admins_empty_array(self) -> None:
        meeting = self.basic_test({"admin_ids": []})
        assert "admin_ids" not in meeting

    def test_create_set_as_template(self) -> None:
        meeting = self.basic_test({"set_as_template": True})
        assert meeting.get("template_for_organization_id") == 1
        self.assert_model_exists("organization/1", {"template_meeting_ids": [1]})

    def test_create_no_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                },
                "committee/1": {"name": "test_committee", "user_ids": [1, 2]},
                "group/1": {},
                "user/2": {},
            }
        )

        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "Missing CommitteeManagementLevel: can_manage" in response.json["message"]
        )

    def test_create_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "committee_$can_manage_management_level": [1],
                }
            }
        )
        self.basic_test({})

    def test_create_with_admin_ids_and_permissions_cml(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": None,
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "committee_$can_manage_management_level": [1],
                }
            }
        )
        meeting = self.basic_test({"admin_ids": [2]})
        assert meeting.get("user_ids") == [2]
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists(
            "user/2", {f"group_${meeting['id']}_ids": [admin_group_id]}
        )

    def test_create_with_admin_ids_and_permissions_oml(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                    "committee_$can_manage_management_level": [],
                }
            }
        )
        meeting = self.basic_test({"admin_ids": [2]})
        assert meeting.get("user_ids") == [2]
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists(
            "user/2", {f"group_${meeting['id']}_ids": [admin_group_id]}
        )

    def test_create_limit_of_meetings_reached(self) -> None:
        self.set_models(
            {
                "organization/1": {"limit_of_meetings": 1, "active_meeting_ids": [1]},
                "committee/1": {"organization_id": 1},
            }
        )
        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "You cannot create a new meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )
