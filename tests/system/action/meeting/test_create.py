from typing import Any

from openslides_backend.i18n.translator import Translator
from openslides_backend.i18n.translator import translate as _
from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MeetingCreateActionTest(BaseActionTestCase):
    def basic_test(
        self,
        datapart: dict[str, Any],
        set_400_str: str = "",
        orga_settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if orga_settings is None:
            orga_settings = {}
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 0,
                    "active_meeting_ids": [],
                    **orga_settings,
                },
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
                "language": "en",
                **datapart,
            },
        )
        if set_400_str:
            self.assert_status_code(response, 400)
            assert set_400_str == response.json["message"]
            return {}
        else:
            self.assert_status_code(response, 200)
            return self.get_model("meeting/1")

    def test_create_simple_and_complex_workflow(self) -> None:
        self.basic_test(dict())
        self.assert_model_exists(
            "meeting/1",
            {
                "name": "test_name",
                "committee_id": 1,
                "group_ids": [2, 3, 4, 5],
                "default_group_id": 2,
                "admin_group_id": 3,
                "motion_workflow_ids": [1, 2],
                "motions_default_workflow_id": 1,
                "motions_default_amendment_workflow_id": 1,
                "motion_state_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
                "list_of_speakers_countdown_id": 1,
                "poll_countdown_id": 2,
                "projector_countdown_warning_time": 0,
                "organization_tag_ids": [3],
                "is_active_in_organization_id": 1,
                "assignment_poll_default_group_ids": [4],
                "motion_poll_default_group_ids": [4],
                "topic_poll_default_group_ids": [4],
                **{field: [1] for field in Meeting.all_default_projectors()},
            },
        )
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"active_meeting_ids": [1]})
        self.assert_model_exists("group/2", {"name": "Default"})
        self.assert_model_exists("group/3", {"name": "Admin"})
        self.assert_model_exists("group/4", {"name": "Delegates"})
        self.assert_model_exists("group/5", {"name": "Staff"})
        self.assert_model_exists(
            "motion_workflow/1",
            {
                "name": "Simple Workflow",
                "meeting_id": 1,
                "default_workflow_meeting_id": 1,
                "default_amendment_workflow_meeting_id": 1,
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
                "state_ids": [5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
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
        external_id = "external"
        meeting = self.basic_test(
            {
                "description": "RRfnzxHA",
                "location": "LSFHPTgE",
                "start_time": 1608120653,
                "end_time": 1608121653,
                "external_id": external_id,
            }
        )
        assert meeting.get("description") == "RRfnzxHA"
        assert meeting.get("location") == "LSFHPTgE"
        assert meeting.get("start_time") == 1608120653
        assert meeting.get("end_time") == 1608121653
        assert meeting.get("external_id") == external_id
        # check two defaults:
        assert meeting.get("assignment_poll_default_type") == "pseudoanonymous"
        assert meeting.get("assignment_poll_default_method") == "Y"

    def test_create_check_users(self) -> None:
        meeting = self.basic_test({"user_ids": [2]})
        assert meeting.get("user_ids") == [2]
        default_group_id = meeting.get("default_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": meeting["id"],
                "user_id": 2,
                "group_ids": [default_group_id],
            },
        )

    def test_create_check_admins(self) -> None:
        meeting = self.basic_test({"admin_ids": [2]})
        assert meeting.get("user_ids") == [2]
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": meeting["id"], "user_id": 2, "group_ids": [admin_group_id]},
        )

    def test_create_with_same_user_in_users_and_admins(self) -> None:
        meeting = self.basic_test({"user_ids": [2], "admin_ids": [2]})
        assert meeting.get("user_ids") == [2]
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": meeting["id"], "user_id": 2, "group_ids": [admin_group_id]},
        )

    def test_create_multiple_users(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 0,
                    "active_meeting_ids": [],
                },
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
                "language": "en",
            },
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
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
        self.assertCountEqual(meeting.get("user_ids", []), [1, 2, 3])
        committee = self.get_model("committee/1")
        self.assertCountEqual(committee.get("user_ids", []), [1, 2, 3])

    def test_create_with_admins_empty_array(self) -> None:
        meeting = self.basic_test({"admin_ids": []})
        assert "admin_ids" not in meeting

    def test_create_set_as_template(self) -> None:
        meeting = self.basic_test({"set_as_template": True})
        assert meeting.get("template_for_organization_id") == 1
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
            set_400_str="data.name must be shorter than or equal to 100 characters",
        )

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
                "language": "en",
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "Missing permission: CommitteeManagementLevel can_manage in committee 1"
            in response.json["message"]
        )

    def test_create_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "committee_management_ids": [1],
                }
            }
        )
        self.basic_test({})

    def test_create_with_admin_ids_and_permissions_cml(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": None,
                    "committee_management_ids": [1],
                }
            }
        )
        meeting = self.basic_test({"admin_ids": [2]})
        assert meeting.get("user_ids") == [2]
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": meeting["id"], "user_id": 2, "group_ids": [admin_group_id]},
        )

    def test_create_with_admin_ids_and_permissions_oml(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                    "committee_management_ids": [],
                }
            }
        )
        meeting = self.basic_test({"admin_ids": [2]})
        assert meeting.get("user_ids") == [2]
        admin_group_id = meeting.get("admin_group_id")
        self.assert_model_exists("user/2", {"meeting_user_ids": [1]})
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": meeting["id"], "user_id": 2, "group_ids": [admin_group_id]},
        )

    def test_create_limit_of_meetings_reached(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 1,
                    "active_meeting_ids": [1],
                },
                "committee/1": {"organization_id": 1},
            }
        )
        response = self.request(
            "meeting.create",
            {
                "name": "test_name",
                "committee_id": 1,
                "language": "en",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "You cannot create a new meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )

    def test_create_language_and_external_id(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 0,
                    "active_meeting_ids": [],
                    "default_language": "en",
                },
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
                "language": "de",
            },
        )
        self.assert_status_code(response, 200)
        Translator.set_translation_language("de")
        self.assert_model_exists(
            "meeting/1",
            {
                "description": "Präsentations- und Versammlungssystem",
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
        for i, name in enumerate(["Default", "Admin", "Delegates", "Staff"], 2):
            self.assert_model_exists(
                f"group/{i}", {"name": _(name), "external_id": name}
            )

    def test_create_external_id_not_unique(self) -> None:
        external_id = "external"
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "external_id": external_id},
                "committee/1": {"name": "test committee", "organization_id": 1},
            }
        )
        response = self.request(
            "meeting.create",
            {
                "name": "meeting2",
                "committee_id": 1,
                "language": "en",
                "external_id": external_id,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The external_id of the meeting is not unique in the committee scope.",
            response.json["message"],
        )

    def test_create_external_id_empty_special_case(self) -> None:
        external_id = ""
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "external_id": external_id},
                "committee/1": {"name": "test committee", "organization_id": 1},
            }
        )
        response = self.request(
            "meeting.create",
            {
                "name": "meeting2",
                "committee_id": 1,
                "language": "de",
                "external_id": external_id,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "name": "meeting2",
                "committee_id": 1,
                "language": "de",
                "external_id": external_id,
            },
        )

    def test_enable_duplicate_mandatory(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": None,
                    "committee_management_ids": [1],
                }
            }
        )
        self.basic_test(
            {},
            set_400_str="You cannot create a new meeting, because you need to use a template.",
            orga_settings={"require_duplicate_from": True},
        )
