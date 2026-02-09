from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from openslides_backend.i18n.translator import Translator
from openslides_backend.i18n.translator import translate as _
from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MeetingCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_committee()
        self.create_user("user/2")
        self.set_models(
            {
                "organization_tag/3": {
                    "name": "TEST",
                    "color": "#eeeeee",
                    "organization_id": 1,
                },
            }
        )
        self.base_action_data = {
            "name": "test_name",
            "committee_id": 1,
            "organization_tag_ids": [3],
            "language": "en",
            "admin_ids": [1],
        }

    def basic_test(
        self, meeting_action_data: dict[str, Any] = {}, set_400_str: str = ""
    ) -> None:
        response = self.request(
            "meeting.create", {**self.base_action_data, **meeting_action_data}
        )
        if set_400_str:
            self.assert_status_code(response, 400)
            assert set_400_str == response.json["message"]
        else:
            self.assert_status_code(response, 200)

    def test_create_simple_and_complex_workflow(self) -> None:
        self.basic_test()
        self.assert_model_exists(
            "meeting/1",
            {
                "name": "test_name",
                "committee_id": 1,
                "group_ids": [1, 2, 3, 4],
                "default_group_id": 1,
                "admin_group_id": 2,
                "motion_workflow_ids": [1, 2],
                "motions_default_workflow_id": 1,
                "motions_default_amendment_workflow_id": 1,
                "motion_state_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
                "list_of_speakers_countdown_id": 1,
                "poll_countdown_id": 2,
                "projector_countdown_warning_time": 0,
                "organization_tag_ids": [3],
                "is_active_in_organization_id": 1,
                "assignment_poll_default_group_ids": [3],
                "motion_poll_default_group_ids": [3],
                "topic_poll_default_group_ids": [3],
                "motion_poll_projection_name_order_first": "last_name",
                "motion_poll_projection_max_columns": 6,
                **{field: [1] for field in Meeting.all_default_projectors()},
            },
        )
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"active_meeting_ids": [1]})
        self.assert_model_exists("group/1", {"name": "Default"})
        self.assert_model_exists("group/2", {"name": "Admin"})
        self.assert_model_exists("group/3", {"name": "Delegates"})
        self.assert_model_exists("group/4", {"name": "Staff"})
        self.assert_model_exists(
            "motion_workflow/1",
            {
                "name": "Simple Workflow",
                "meeting_id": 1,
                "default_workflow_meeting_id": 1,
                "default_amendment_workflow_meeting_id": 1,
                "state_ids": [1, 2, 3, 4],
                "first_state_id": 1,
                "sequential_number": 1,
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
                "state_ids": [5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
                "first_state_id": 5,
                "sequential_number": 2,
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
            {"name": "referred to", "previous_state_ids": [7]},
        )
        self.assert_model_exists(
            "motion_state/14",
            {"name": "not permitted", "previous_state_ids": [6]},
        )
        self.assert_model_exists(
            "projector/1",
            {
                "name": "Default projector",
                "meeting_id": 1,
                "used_as_reference_projector_meeting_id": 1,
                "sequential_number": 1,
                **{field: 1 for field in Meeting.reverse_default_projectors()},
            },
        )
        self.assert_model_exists(
            "projector_countdown/1",
            {
                "title": "Speaking time",
                "meeting_id": 1,
                "used_as_list_of_speakers_countdown_meeting_id": 1,
                "default_time": 60,
                "countdown_time": 60,
            },
        )
        self.assert_model_exists(
            "projector_countdown/2",
            {
                "title": "Voting",
                "meeting_id": 1,
                "used_as_poll_countdown_meeting_id": 1,
                "default_time": 60,
                "countdown_time": 60,
            },
        )

    def test_check_action_data_fields(self) -> None:
        """Also checks defaults for assignment_poll and motion_poll."""
        external_id = "external"
        self.basic_test(
            {
                "description": "RRfnzxHA",
                "location": "LSFHPTgE",
                "start_time": 1608120653,
                "end_time": 1608121653,
                "external_id": external_id,
            }
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "description": "RRfnzxHA",
                "location": "LSFHPTgE",
                "start_time": datetime.fromtimestamp(1608120653, ZoneInfo("UTC")),
                "end_time": datetime.fromtimestamp(1608121653, ZoneInfo("UTC")),
                "external_id": external_id,
                "assignment_poll_default_type": "pseudoanonymous",
                "assignment_poll_default_method": "Y",
                "motion_poll_default_type": "pseudoanonymous",
                "motion_poll_default_method": "YNA",
            },
        )

    def test_create_check_users(self) -> None:
        self.basic_test({"user_ids": [2]})
        meeting = self.assert_model_exists("meeting/1", {"user_ids": [1, 2]})
        default_group_id = meeting.get("default_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [2]})
        self.assert_model_exists(
            "meeting_user/2",
            {"meeting_id": 1, "user_id": 2, "group_ids": [default_group_id]},
        )

    def test_create_check_admins(self) -> None:
        self.basic_test({"admin_ids": [2]})
        meeting = self.assert_model_exists("meeting/1", {"user_ids": [2]})
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": meeting["id"], "user_id": 2, "group_ids": [admin_group_id]},
        )

    def test_create_with_same_user_in_users_and_admins(self) -> None:
        self.basic_test({"user_ids": [2], "admin_ids": [2]})
        meeting = self.assert_model_exists("meeting/1", {"user_ids": [2]})
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": meeting["id"], "user_id": 2, "group_ids": [admin_group_id]},
        )

    def test_create_multiple_users(self) -> None:
        self.create_user("user/3")
        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
                "user_ids": [2, 3],
                "admin_ids": [1],
                "language": "en",
            },
        )
        self.assert_status_code(response, 200)
        meeting = self.assert_model_exists("meeting/1", {"user_ids": [1, 2, 3]})
        default_group_id = meeting.get("default_group_id")
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists(
            "user/2", {"meeting_user_ids": [2], "committee_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": 1, "user_id": 1, "group_ids": [admin_group_id]},
        )
        self.assert_model_exists(
            "user/3", {"meeting_user_ids": [3], "committee_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/2",
            {"meeting_id": 1, "user_id": 2, "group_ids": [default_group_id]},
        )
        self.assert_model_exists(
            "user/1", {"meeting_user_ids": [1], "committee_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/3",
            {"meeting_id": 1, "user_id": 3, "group_ids": [default_group_id]},
        )
        self.assert_model_exists("committee/1", {"user_ids": [1, 2, 3]})

    def test_create_with_admins_empty_array(self) -> None:
        self.basic_test(
            {"admin_ids": []}, "Cannot create non-template meeting without admin_ids"
        )

    def test_create_with_no_admins(self) -> None:
        del self.base_action_data["admin_ids"]
        self.basic_test(
            set_400_str="Cannot create non-template meeting without admin_ids"
        )

    def test_create_set_as_template_with_admins_empty_array(self) -> None:
        self.basic_test({"admin_ids": [], "set_as_template": True})
        self.assert_model_exists("meeting/1", {"template_for_organization_id": 1})
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"template_meeting_ids": [1]})

    def test_create_set_as_template_with_no_admins_array(self) -> None:
        del self.base_action_data["admin_ids"]
        self.basic_test({"set_as_template": True})
        self.assert_model_exists("meeting/1", {"template_for_organization_id": 1})
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"template_meeting_ids": [1]})

    def test_create_set_as_template(self) -> None:
        self.basic_test({"set_as_template": True})
        self.assert_model_exists("meeting/1", {"template_for_organization_id": 1})
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"template_meeting_ids": [1]})

    def test_create_set_only_one_time_1(self) -> None:
        self.basic_test(
            {"start_time": 160000},
            set_400_str="Only one of start_time and end_time is not allowed.",
        )

    def test_create_set_only_one_time_2(self) -> None:
        self.basic_test(
            {"end_time": 170000},
            set_400_str="Only one of start_time and end_time is not allowed.",
        )

    def test_create_empty_times(self) -> None:
        self.basic_test({"start_time": None, "end_time": None})

    def test_create_name_too_long(self) -> None:
        self.basic_test(
            {"name": "A" * 101},
            set_400_str="Action meeting.create: data.name must be shorter than or equal to 100 characters",
        )

    def test_create_no_permissions(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
                "language": "en",
                "admin_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "Missing permission: CommitteeManagementLevel can_manage in committee 1"
            in response.json["message"]
        )

    def test_create_permissions(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        self.set_committee_management_level([1])
        self.basic_test()

    def test_create_with_admin_ids_and_permissions_cml(self) -> None:
        self.set_organization_management_level(None)
        self.set_committee_management_level([1])
        self.basic_test({"admin_ids": [2]})
        meeting = self.assert_model_exists("meeting/1", {"user_ids": [2]})
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": meeting["id"], "user_id": 2, "group_ids": [admin_group_id]},
        )

    def test_create_with_admin_ids_and_permissions_oml(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        self.basic_test({"admin_ids": [2]})
        meeting = self.assert_model_exists("meeting/1", {"user_ids": [2]})
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": meeting["id"], "user_id": 2, "group_ids": [admin_group_id]},
        )

    def test_create_without_admin_ids_and_permissions_oml(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        self.basic_test()
        meeting = self.assert_model_exists("meeting/1", {"user_ids": [1]})
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists("user/1", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": meeting["id"], "user_id": 1, "group_ids": [admin_group_id]},
        )

    def test_create_limit_of_meetings_reached(self) -> None:
        self.set_models({ONE_ORGANIZATION_FQID: {"limit_of_meetings": 1}})
        self.create_meeting()
        self.basic_test(
            set_400_str="You cannot create a new meeting, because you reached your limit of 1 active meetings."
        )

    def test_create_language_and_external_id(self) -> None:
        self.set_models({ONE_ORGANIZATION_FQID: {"default_language": "en"}})
        self.basic_test({"language": "de"})
        Translator.set_translation_language("de")
        self.assert_model_exists(
            "meeting/1",
            {
                "description": None,
                "welcome_title": "Willkommen bei OpenSlides",
                "welcome_text": "Platz für Ihren Begrüßungstext.",
                "motions_preamble": "Die Versammlung möge beschließen:",
                "motions_export_title": "Anträge",
                "assignments_export_title": "Wahlen",
                "users_pdf_welcometitle": "Willkommen bei OpenSlides",
                "users_pdf_welcometext": "[Platz für Ihren Begrüßungs- und Hilfetext.]",
                "users_email_sender": "OpenSlides",
                "users_email_subject": "OpenSlides-Zugangsdaten",
                "users_email_body": "Hallo {name},\n\nhier ist Ihr persönlicher OpenSlides-Zugang:\n\n{url}\nBenutzername: {username}\nPasswort: {password}\n\n\nDiese E-Mail wurde automatisch erstellt.",
            },
        )
        for i, name in enumerate(["Default", "Admin", "Delegates", "Staff"], 1):
            self.assert_model_exists(
                f"group/{i}", {"name": _(name), "external_id": name}
            )

    def test_create_external_id_not_unique(self) -> None:
        external_id = "external"
        self.create_meeting(meeting_data=({"external_id": external_id}))
        self.basic_test(
            {"external_id": external_id},
            set_400_str="The external id of the meeting is not unique in the organization scope. Send a differing external id with this request.",
        )
        self.assert_model_not_exists("meeting/2")

    def test_create_external_id_empty_special_case(self) -> None:
        external_id = ""
        self.create_meeting(
            meeting_data=({"committee_id": 1, "external_id": external_id})
        )
        self.base_action_data.update({"external_id": external_id})
        self.basic_test()
        self.assert_model_exists("meeting/2", {"external_id": external_id})

    def test_enable_duplicate_mandatory(self) -> None:
        self.set_organization_management_level(None)
        self.set_committee_management_level([1])
        self.set_models({ONE_ORGANIZATION_FQID: {"require_duplicate_from": True}})
        self.basic_test(
            set_400_str="You cannot create a new meeting, because you need to use a template.",
        )
