from typing import Any, Dict, List, Tuple, cast

from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase
from tests.util import Response


class MeetingUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: Dict[str, Dict[str, Any]] = {
            "committee/1": {"name": "test_committee"},
            "meeting/1": {
                "name": "test_name",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
                "default_group_id": 1,
                "admin_group_id": 1,
                "projector_ids": [1],
                "reference_projector_id": 1,
                "default_projector_$_id": Meeting.default_projector__id.replacement_enum,
                **{
                    f"default_projector_${name}_id": 1
                    for name in cast(
                        List[str], Meeting.default_projector__id.replacement_enum
                    )
                },
            },
            "projector/1": {
                "name": "Projector 1",
                "meeting_id": 1,
                "used_as_reference_projector_meeting_id": 1,
                "used_as_default_$_in_meeting_id": Meeting.default_projector__id.replacement_enum,
                **{
                    f"used_as_default_${name}_in_meeting_id": 1
                    for name in cast(
                        List[str], Meeting.default_projector__id.replacement_enum
                    )
                },
            },
        }

    def basic_test(
        self, datapart: Dict[str, Any], check_200: bool = True
    ) -> Tuple[Dict[str, Any], Response]:
        self.set_models(
            {
                "committee/1": {"name": "test_committee"},
                "group/1": {},
                "meeting/1": {
                    "name": "test_name",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "default_group_id": 1,
                    "projector_ids": [1],
                    "reference_projector_id": 1,
                    "default_projector_$_id": Meeting.default_projector__id.replacement_enum,
                    **{
                        f"default_projector_${name}_id": 1
                        for name in cast(
                            List[str], Meeting.default_projector__id.replacement_enum
                        )
                    },
                },
                "projector/1": {
                    "name": "Projector 1",
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    "used_as_default_$_in_meeting_id": Meeting.default_projector__id.replacement_enum,
                    **{
                        f"used_as_default_${name}_in_meeting_id": 1
                        for name in cast(
                            List[str], Meeting.default_projector__id.replacement_enum
                        )
                    },
                },
            }
        )
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                **datapart,
            },
        )
        if check_200:
            self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        assert meeting.get("name") == "test_name"
        assert meeting.get("committee_id") == 1
        return meeting, response

    def test_update_some_fields_export(self) -> None:
        meeting, _ = self.basic_test(
            {
                "export_csv_encoding": "utf-8",
                "export_csv_separator": ",",
                "export_pdf_pagenumber_alignment": "center",
                "export_pdf_fontsize": 11,
                "export_pdf_pagesize": "A4",
            }
        )
        assert meeting.get("export_csv_encoding") == "utf-8"
        assert meeting.get("export_csv_separator") == ","
        assert meeting.get("export_pdf_pagenumber_alignment") == "center"
        assert meeting.get("export_pdf_fontsize") == 11
        assert meeting.get("export_pdf_pagesize") == "A4"

    def test_update_some_fields_user_email(self) -> None:
        meeting, _ = self.basic_test(
            {
                "users_email_sender": "test@example.com",
                "users_email_replyto": "test2@example.com",
                "users_email_subject": "blablabla",
                "users_email_body": "testtesttest",
            }
        )
        assert meeting.get("users_email_sender") == "test@example.com"
        assert meeting.get("users_email_replyto") == "test2@example.com"
        assert meeting.get("users_email_subject") == "blablabla"
        assert meeting.get("users_email_body") == "testtesttest"

    def test_update_projector_related_fields(self) -> None:
        self.set_models(
            {
                "projector/2": {
                    "name": "Projector 2",
                    "meeting_id": 1,
                },
                "meeting/1": {
                    "projector_ids": [1, 2],
                },
            }
        )
        self.basic_test(
            {"reference_projector_id": 2, "default_projector_$_id": {"topics": 2}}
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "reference_projector_id": 2,
                "default_projector_$topics_id": 2,
                "default_projector_$motion_id": 1,
            },
        )
        self.assert_model_exists(
            "projector/1",
            {
                "used_as_reference_projector_meeting_id": None,
                "used_as_default_$topics_in_meeting_id": None,
                "used_as_default_$motion_in_meeting_id": 1,
            },
        )
        self.assert_model_exists(
            "projector/2",
            {
                "used_as_reference_projector_meeting_id": 1,
                "used_as_default_$topics_in_meeting_id": 1,
                "used_as_default_$motion_in_meeting_id": None,
            },
        )

    def test_update_reference_projector_to_null_error(self) -> None:
        _, response = self.basic_test({"reference_projector_id": None}, check_200=False)
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.reference_projector_id must be integer", response.json["message"]
        )

    def test_update_reference_projector_to_not_existing_projector_error(self) -> None:
        _, response = self.basic_test({"reference_projector_id": 10}, check_200=False)
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['projector/10']",
            response.json["message"],
        )

    def test_update_reference_projector_to_projector_from_wrong_meeting_error(
        self,
    ) -> None:
        self.set_models(
            {
                "projector/2": {
                    "name": "Projector 2",
                    "meeting_id": 2,
                },
            }
        )
        _, response = self.basic_test({"reference_projector_id": 2}, check_200=False)
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['projector/2']",
            response.json["message"],
        )

    def test_update_default_projector_to_not_existing_replacement_error(self) -> None:
        _, response = self.basic_test(
            {"default_projector_$_id": {"not_existing": 1}}, check_200=False
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.default_projector_$_id must not contain {'not_existing'} properties",
            response.json["message"],
        )

    def test_update_default_projector_to_null_error(self) -> None:
        _, response = self.basic_test(
            {"default_projector_$_id": {"topics": None}}, check_200=False
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.default_projector_$_id.topics must be integer",
            response.json["message"],
        )

    def test_update_default_projector_to_not_existing_projector_error(self) -> None:
        _, response = self.basic_test(
            {"default_projector_$_id": {"topics": 2}}, check_200=False
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['projector/2']",
            response.json["message"],
        )

    def test_update_default_projector_to_projector_from_wrong_meeting_error(
        self,
    ) -> None:
        self.set_models(
            {
                "projector/2": {
                    "name": "Projector 2",
                    "meeting_id": 2,
                },
            }
        )
        _, response = self.basic_test(
            {"default_projector_$_id": {"topics": 2}}, check_200=False
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['projector/2']",
            response.json["message"],
        )

    def test_update_conference_enable_helpdesk(self) -> None:
        meeting, _ = self.basic_test({"conference_enable_helpdesk": True})
        assert meeting.get("conference_enable_helpdesk") is True

    def test_update_applause(self) -> None:
        self.basic_test(
            {
                "applause_enable": True,
                "applause_type": "applause-type-particles",
                "applause_show_level": True,
                "applause_min_amount": 2,
                "applause_max_amount": 3,
                "applause_timeout": 6,
                "applause_particle_image_url": "test",
            }
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "applause_enable": True,
                "applause_type": "applause-type-particles",
                "applause_show_level": True,
                "applause_min_amount": 2,
                "applause_max_amount": 3,
                "applause_timeout": 6,
                "applause_particle_image_url": "test",
            },
        )

    def test_update_poll_default_backend_fields(self) -> None:
        self.basic_test(
            {
                "motion_poll_default_backend": "long",
                "assignment_poll_default_backend": "long",
                "poll_default_backend": "long",
            }
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "motion_poll_default_backend": "long",
                "assignment_poll_default_backend": "long",
                "poll_default_backend": "long",
            },
        )

    def test_update_group_a_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_models, "meeting.update", {"id": 1, "welcome_title": "Hallo"}
        )

    def test_update_group_a_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "welcome_title": "Hallo"},
            Permissions.Meeting.CAN_MANAGE_SETTINGS,
        )

    def test_update_group_b_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_models, "meeting.update", {"id": 1, "present_user_ids": [2]}
        )

    def test_update_group_b_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "present_user_ids": [2]},
            Permissions.User.CAN_MANAGE,
        )

    def test_update_group_c_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_models, "meeting.update", {"id": 1, "reference_projector_id": 1}
        )

    def test_update_group_c_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "reference_projector_id": 1},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_update_group_d_no_permissions(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [])
        self.set_models(self.test_models)
        response = self.request(
            "meeting.update",
            {"id": 1, "enable_anonymous": True},
        )
        self.assert_status_code(response, 403)
        assert "Missing permission:" in response.json["message"]

    def test_update_group_d_permissions(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [1])
        self.set_models(self.test_models)
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "custom_translations": {"motion": "Antrag", "assignment": "Zuordnung"},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {"custom_translations": {"motion": "Antrag", "assignment": "Zuordnung"}},
        )

    def test_update_group_e_no_permission(self) -> None:
        self.set_models({"organization_tag/1": {}})
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_models(self.test_models)
        response = self.request(
            "meeting.update", {"id": 1, "organization_tag_ids": [1]}
        )
        self.assert_status_code(response, 403)
        assert "Missing permission:" in response.json["message"]

    def test_update_group_e_permission(self) -> None:
        self.set_models({"organization_tag/1": {}})
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "organization_tag_ids": [1]},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )

    def test_update_group_f_no_permission(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {
                "id": 1,
                "jitsi_domain": "test",
                "jitsi_room_name": "room1",
                "jitsi_room_password": "blablabla",
                "enable_chat": True,
            },
        )

    def test_update_group_f_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {
                "id": 1,
                "jitsi_domain": "test",
                "jitsi_room_name": "room1",
                "jitsi_room_password": "blablabla",
                "enable_chat": True,
            },
            OrganizationManagementLevel.SUPERADMIN,
        )

    def test_update_list_of_speakers_enable_point_of_order_speakers(self) -> None:
        self.basic_test({"list_of_speakers_enable_point_of_order_speakers": True})
        self.assert_model_exists(
            "meeting/1", {"list_of_speakers_enable_point_of_order_speakers": True}
        )

    def test_update_with_user(self) -> None:
        self.set_models(
            {
                "committee/1": {"meeting_ids": [3]},
                "meeting/3": {
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "group_ids": [11],
                    "admin_group_id": 11,
                },
                "group/11": {"meeting_id": 3, "admin_group_for_meeting_id": 3},
                "user/4": {},
            }
        )
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        self.set_user_groups(1, [11])
        response = self.request_json(
            [
                {
                    "action": "meeting.update",
                    "data": [
                        {
                            "name": "meeting",
                            "welcome_title": "title",
                            "welcome_text": "",
                            "description": "",
                            "location": "",
                            "start_time": 1623016800,
                            "end_time": 1623016800,
                            "enable_anonymous": True,
                            "organization_tag_ids": [],
                            "id": 3,
                        }
                    ],
                },
                {
                    "action": "user.update",
                    "data": [{"id": 4, "group_$_ids": {"3": [11]}}],
                },
            ]
        )
        self.assert_status_code(response, 200)
