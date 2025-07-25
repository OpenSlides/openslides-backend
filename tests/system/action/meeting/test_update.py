from typing import Any

from openslides_backend.i18n.translator import Translator
from openslides_backend.i18n.translator import translate as _
from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase
from tests.util import Response


class MeetingUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            ONE_ORGANIZATION_FQID: {"enable_anonymous": True},
            "committee/1": {"name": "test_committee"},
            "meeting/1": {
                "name": "test_name",
                "is_active_in_organization_id": 1,
                "committee_id": 1,
                "default_group_id": 1,
                "admin_group_id": 1,
                "projector_ids": [1],
                "reference_projector_id": 1,
                "language": "en",
                **{field: [1] for field in Meeting.all_default_projectors()},
            },
            "projector/1": {
                "name": "Projector 1",
                "meeting_id": 1,
                "used_as_reference_projector_meeting_id": 1,
                **{field: 1 for field in Meeting.reverse_default_projectors()},
            },
            "group/1": {
                "admin_group_for_meeting_id": 1,
                "default_group_for_meeting_id": 1,
                "meeting_id": 1,
            },
        }

    def basic_test(
        self, datapart: dict[str, Any], check_200: bool = True
    ) -> tuple[dict[str, Any], Response]:
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
                    "language": "en",
                    **{field: [1] for field in Meeting.all_default_projectors()},
                },
                "projector/1": {
                    "name": "Projector 1",
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    **{field: 1 for field in Meeting.reverse_default_projectors()},
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
                "users_email_replyto": "  test2@example.com  ",
                "users_email_subject": "blablabla",
                "users_email_body": "testtesttest",
                "users_forbid_delegator_as_submitter": True,
                "users_forbid_delegator_in_list_of_speakers": False,
            }
        )
        assert meeting.get("users_email_sender") == "test@example.com"
        assert meeting.get("users_email_replyto") == "test2@example.com"
        assert meeting.get("users_email_subject") == "blablabla"
        assert meeting.get("users_email_body") == "testtesttest"
        assert meeting.get("users_forbid_delegator_as_submitter")
        assert not meeting.get("users_forbid_delegator_in_list_of_speakers")

    def test_update_motion_poll_projection(self) -> None:
        self.basic_test(
            {
                "motion_poll_projection_name_order_first": "first_name",
                "motion_poll_projection_max_columns": 5,
            }
        )

    def test_update_motion_poll_projection_invalid_data_error(self) -> None:
        meeting, response = self.basic_test(
            {
                "motion_poll_projection_name_order_first": "best_name",
            },
            False,
        )
        self.assert_status_code(response, 400)
        assert (
            "data.motion_poll_projection_name_order_first must be one of ['first_name', 'last_name']"
            in response.json["message"]
        )

    def test_update_broken_email(self) -> None:
        meeting, response = self.basic_test({"users_email_replyto": "broken@@"}, False)
        self.assert_status_code(response, 400)
        assert "users_email_replyto must be valid email." in response.json["message"]

    def test_update_broken_sender(self) -> None:
        meeting, response = self.basic_test(
            {"users_email_sender": "Openslides[Test"}, False
        )
        self.assert_status_code(response, 400)
        assert (
            "users_email_sender must not contain '[', ']', '\\'."
            in response.json["message"]
        )

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
            {
                "reference_projector_id": 2,
                "default_projector_topic_ids": [2],
                "default_projector_current_los_ids": [1, 2],
            }
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "reference_projector_id": 2,
                "default_projector_topic_ids": [2],
                "default_projector_motion_ids": [1],
                "default_projector_current_los_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "projector/1",
            {
                "used_as_reference_projector_meeting_id": None,
                "used_as_default_projector_for_topic_in_meeting_id": None,
                "used_as_default_projector_for_motion_in_meeting_id": 1,
                "used_as_default_projector_for_current_los_in_meeting_id": 1,
            },
        )
        self.assert_model_exists(
            "projector/2",
            {
                "used_as_reference_projector_meeting_id": 1,
                "used_as_default_projector_for_topic_in_meeting_id": 1,
                "used_as_default_projector_for_motion_in_meeting_id": None,
                "used_as_default_projector_for_current_los_in_meeting_id": 1,
            },
        )

    def test_update_projector_related_fields2(self) -> None:
        self.test_update_projector_related_fields()
        self.request(
            "meeting.update",
            {
                "id": 1,
                "default_projector_current_los_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "reference_projector_id": 2,
                "default_projector_topic_ids": [2],
                "default_projector_motion_ids": [1],
                "default_projector_current_los_ids": [2],
            },
        )
        self.assert_model_exists(
            "projector/1",
            {
                "used_as_reference_projector_meeting_id": None,
                "used_as_default_projector_for_topic_in_meeting_id": None,
                "used_as_default_projector_for_motion_in_meeting_id": 1,
                "used_as_default_projector_for_current_los_in_meeting_id": None,
            },
        )
        self.assert_model_exists(
            "projector/2",
            {
                "used_as_reference_projector_meeting_id": 1,
                "used_as_default_projector_for_topic_in_meeting_id": 1,
                "used_as_default_projector_for_motion_in_meeting_id": None,
                "used_as_default_projector_for_current_los_in_meeting_id": 1,
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
            "Model 'projector/10' does not exist.",
            response.json["message"],
        )

    def test_update_reference_projector_to_internal_projector_error(self) -> None:
        self.set_models(
            {
                "projector/2": {
                    "name": "Projector 2",
                    "is_internal": True,
                    "meeting_id": 1,
                },
                "meeting/1": {
                    "projector_ids": [1, 2],
                },
            }
        )
        _, response = self.basic_test({"reference_projector_id": 2}, check_200=False)
        self.assert_status_code(response, 400)
        self.assertIn(
            "An internal projector cannot be set as reference projector.",
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

    def test_update_default_projector_to_not_existing_option_error(self) -> None:
        _, response = self.basic_test(
            {"default_projector_non_existing_ids": [1]}, check_200=False
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'default_projector_non_existing_ids'} properties",
            response.json["message"],
        )

    def test_update_default_projector_to_null_error(self) -> None:
        _, response = self.basic_test(
            {"default_projector_topic_ids": None}, check_200=False
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.default_projector_topic_ids must be array",
            response.json["message"],
        )

    def test_update_default_projector_to_not_existing_projector_error(self) -> None:
        _, response = self.basic_test(
            {"default_projector_topic_ids": [2]}, check_200=False
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
            {"default_projector_topic_ids": [2]}, check_200=False
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

    def test_update_poll_default_live_voting_enabled(self) -> None:
        self.basic_test({"poll_default_live_voting_enabled": True})
        self.assert_model_exists(
            "meeting/1",
            {"poll_default_live_voting_enabled": True},
        )

    def test_update_motions_block_slide_columns(self) -> None:
        self.basic_test(
            {
                "motions_block_slide_columns": 2,
            },
        )
        self.assert_model_exists("meeting/1", {"motions_block_slide_columns": 2})

    def test_update_topic_poll_default_group(self) -> None:
        self.set_models(self.test_models)
        self.set_models({"group/5": {"meeting_id": 1}})
        response = self.request(
            "meeting.update", {"id": 1, "topic_poll_default_group_ids": [5]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"topic_poll_default_group_ids": [5]})
        self.assert_model_exists("group/5", {"used_as_topic_poll_default_id": 1})

    def test_update_only_one_time_1(self) -> None:
        _, response = self.basic_test({"start_time": 150000}, check_200=False)
        assert (
            "Only one of start_time and end_time is not allowed."
            in response.json["message"]
        )

    def test_update_only_one_time_2(self) -> None:
        _, response = self.basic_test({"end_time": 156000}, check_200=False)
        assert (
            "Only one of start_time and end_time is not allowed."
            in response.json["message"]
        )

    def test_update_only_one_time_one_removal_from_db(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {
                    "start_time": 160000,
                    "end_time": 170000,
                },
            }
        )
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "start_time": None,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Only one of start_time and end_time is not allowed."
            in response.json["message"]
        )

    def test_update_new_meeting_setting(self) -> None:
        meeting, _ = self.basic_test(
            {
                "agenda_show_topic_navigation_on_detail_view": True,
                "motions_hide_metadata_background": True,
                "motions_create_enable_additional_submitter_text": True,
            }
        )
        assert meeting.get("agenda_show_topic_navigation_on_detail_view") is True
        assert meeting.get("motions_hide_metadata_background") is True
        assert meeting.get("motions_create_enable_additional_submitter_text") is True

    def test_update_group_a_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_models, "meeting.update", {"id": 1, "welcome_title": "Hallo"}
        )

    def test_update_group_a_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {
                "id": 1,
                "welcome_title": "Hallo",
                "locked_from_inside": True,
            },
            Permissions.Meeting.CAN_MANAGE_SETTINGS,
        )

    def test_update_group_a_orga_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "welcome_title": "Hallo"},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
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

    def test_update_group_b_permissions_2(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "present_user_ids": [2]},
            Permissions.User.CAN_UPDATE,
        )

    def test_update_group_b_permissions_3(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "present_user_ids": [2]},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )

    def test_update_group_c_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_models, "meeting.update", {"id": 1, "reference_projector_id": 1}
        )

    def test_update_group_c_orga_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "reference_projector_id": 1},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
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

    def test_update_group_d_orga_permissions(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [])
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, self.user_id
        )
        self.set_models(self.test_models)
        response = self.request(
            "meeting.update",
            {"id": 1, "enable_anonymous": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {"enable_anonymous": True},
        )

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
                "external_id": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {
                "custom_translations": {"motion": "Antrag", "assignment": "Zuordnung"},
                "external_id": "test",
            },
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
            },
            OrganizationManagementLevel.SUPERADMIN,
        )

    def test_update_group_f_permissions_organadmin(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {
                "id": 1,
                "jitsi_domain": "test",
                "jitsi_room_name": "room1",
                "jitsi_room_password": "blablabla",
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            fail=True,
        )

    def test_update_with_locked_meeting_group_a(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {
                "id": 1,
                "welcome_title": "Hallo",
                "locked_from_inside": True,
            },
            OrganizationManagementLevel.SUPERADMIN,
            True,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_a_orgaadmin(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {
                "id": 1,
                "welcome_title": "Hallo",
                "locked_from_inside": True,
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            fail=True,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_a_orgaadmin_with_perms(self) -> None:
        self.test_models["group/3"] = {
            "permissions": [Permissions.Meeting.CAN_MANAGE_SETTINGS]
        }
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {
                "id": 1,
                "welcome_title": "Hallo",
                "locked_from_inside": True,
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_b(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "present_user_ids": [2]},
            OrganizationManagementLevel.SUPERADMIN,
            fail=True,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_b_orgaadmin(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "present_user_ids": [2]},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            fail=True,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_c(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "reference_projector_id": 1},
            OrganizationManagementLevel.SUPERADMIN,
            fail=True,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_c_orgaadmin(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "reference_projector_id": 1},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            fail=True,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_c_allowed(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {"id": 1, "reference_projector_id": 1},
            Permissions.Projector.CAN_MANAGE,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_d(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_models(self.test_models)
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        self.set_user_groups(self.user_id, [3])
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "custom_translations": {"motion": "Antrag", "assignment": "Zuordnung"},
                "external_id": "test",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Missing permission: Not admin of this meeting",
            response.json["message"],
        )

    def test_update_with_locked_meeting_group_d_orgaadmin(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_models(self.test_models)
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        self.set_user_groups(self.user_id, [3])
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, self.user_id
        )
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "custom_translations": {"motion": "Antrag", "assignment": "Zuordnung"},
                "external_id": "test",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Missing permission: Not admin of this meeting",
            response.json["message"],
        )

    def test_update_with_locked_meeting_group_d_admin_and_superadmin(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_models(self.test_models)
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        self.set_user_groups(self.user_id, [1])
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "custom_translations": {"motion": "Antrag", "assignment": "Zuordnung"},
                "external_id": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_update_with_locked_meeting_group_e(self) -> None:
        self.set_models(self.test_models)
        self.base_permission_test(
            {"organization_tag/1": {}},
            "meeting.update",
            {"id": 1, "organization_tag_ids": [1]},
            OrganizationManagementLevel.SUPERADMIN,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_e_orgaadmin(self) -> None:
        self.set_models(self.test_models)
        self.base_permission_test(
            {"organization_tag/1": {}},
            "meeting.update",
            {"id": 1, "organization_tag_ids": [1]},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_f(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {
                "id": 1,
                "jitsi_domain": "test",
                "jitsi_room_name": "room1",
                "jitsi_room_password": "blablabla",
            },
            OrganizationManagementLevel.SUPERADMIN,
            lock_meeting=True,
        )

    def test_update_with_locked_meeting_group_f_orgaadmin(self) -> None:
        self.base_permission_test(
            self.test_models,
            "meeting.update",
            {
                "id": 1,
                "jitsi_domain": "test",
                "jitsi_room_name": "room1",
                "jitsi_room_password": "blablabla",
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            fail=True,
            lock_meeting=True,
        )

    def test_update_list_of_speakers_enable_point_of_order_speakers(self) -> None:
        self.basic_test({"list_of_speakers_enable_point_of_order_speakers": True})
        self.assert_model_exists(
            "meeting/1", {"list_of_speakers_enable_point_of_order_speakers": True}
        )

    def test_update_list_of_speakers_closing_disables_point_of_order(
        self,
    ) -> None:
        self.basic_test({"list_of_speakers_closing_disables_point_of_order": True})
        self.assert_model_exists(
            "meeting/1",
            {"list_of_speakers_closing_disables_point_of_order": True},
        )

    def test_update_with_user(self) -> None:
        """Also tests if the anonymous group is created"""
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_anonymous": True},
                "committee/1": {"meeting_ids": [3]},
                "meeting/3": {
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "group_ids": [11],
                    "admin_group_id": 11,
                    "language": "en",
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
                    "data": [{"id": 4, "meeting_id": 3, "group_ids": [11]}],
                },
            ]
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/12",
            {
                "meeting_id": 3,
                "name": "Public",
                "anonymous_group_for_meeting_id": 3,
                "weight": 0,
            },
        )

    def test_update_anonymous_if_disabled_in_orga(self) -> None:
        self.set_models(
            {
                "committee/1": {"meeting_ids": [3]},
                "meeting/3": {
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "group_ids": [11],
                    "admin_group_id": 11,
                    "language": "en",
                },
                "group/11": {"meeting_id": 3, "admin_group_for_meeting_id": 3},
            }
        )
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
            ]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Anonymous users can not be enabled in this organization.",
            response.json["message"],
        )

    def test_update_set_as_template_true(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "set_as_template": True,
            },
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        assert "set_as_template" not in meeting
        assert meeting.get("template_for_organization_id") == 1
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"template_meeting_ids": [1]})

    def test_update_set_as_template_false(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {"template_for_organization_id": 1},
                ONE_ORGANIZATION_FQID: {"template_meeting_ids": [1]},
            }
        )
        self.create_user("bob_admin", [1])
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "set_as_template": False,
            },
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        assert "set_as_template" not in meeting
        assert "template_for_organization_id" not in meeting
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"template_meeting_ids": []})

    def test_update_set_as_template_required_duplicate_from(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {"template_for_organization_id": 1},
                ONE_ORGANIZATION_FQID: {
                    "template_meeting_ids": [1],
                    "require_duplicate_from": True,
                },
            }
        )
        self.set_user_groups(1, [1])
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "set_as_template": False,
            },
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        assert "set_as_template" not in meeting
        assert "template_for_organization_id" not in meeting
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"template_meeting_ids": []})

    def test_update_set_as_template_not_allowed(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {"template_for_organization_id": 1},
                ONE_ORGANIZATION_FQID: {
                    "template_meeting_ids": [1],
                    "require_duplicate_from": True,
                },
                "user/1": {
                    "organization_management_level": None,
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                },
                "committee/1": {"user_ids": [1], "manager_ids": [1]},
            }
        )
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "set_as_template": False,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "A meeting cannot be set as a template by a committee manager if duplicate from is required."
        )

    def test_update_set_as_template_false_template_error(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {"template_for_organization_id": 1},
                ONE_ORGANIZATION_FQID: {"template_meeting_ids": [1]},
            }
        )
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "set_as_template": False,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Can only remove meeting template status if it has at least one administrator."
            in response.json["message"]
        )

    def test_update_check_jitsi_domain_1(self) -> None:
        _, response = self.basic_test(
            {"jitsi_domain": "https://test.com"}, check_200=False
        )
        self.assert_status_code(response, 400)
        assert (
            "It is not allowed to start jitsi_domain with 'https://'."
            in response.json["message"]
        )

    def test_update_check_jitsi_domain_2(self) -> None:
        _, response = self.basic_test({"jitsi_domain": "test.com/"}, check_200=False)
        self.assert_status_code(response, 400)
        assert (
            "It is not allowed to end jitsi_domain with '/'."
            in response.json["message"]
        )

    def test_update_external_id_not_unique(self) -> None:
        external_id = "external"
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "external_id": external_id},
                "meeting/2": {"committee_id": 2},
                "committee/1": {
                    "name": "irrelevant name",
                    "organization_id": 1,
                    "meeting_ids": [1],
                },
                "committee/2": {
                    "name": "irrelevant name",
                    "organization_id": 1,
                    "meeting_ids": [2],
                },
            }
        )
        response = self.request(
            "meeting.update",
            {
                "id": 2,
                "external_id": external_id,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The external id of the meeting is not unique in the organization scope. Send a differing external id with this request.",
            response.json["message"],
        )
        self.assert_model_exists("meeting/2", {"external_id": None, "committee_id": 2})

    def test_update_external_id_self(self) -> None:
        external_id = "external"
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 1,
                    "external_id": external_id,
                    "is_active_in_organization_id": 1,
                    "language": "en",
                },
            }
        )
        response = self.request("meeting.update", {"id": 1, "external_id": external_id})
        self.assert_status_code(response, 200)

    def test_update_cant_lock_template(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "set_as_template": True,
                "locked_from_inside": True,
                "location": "Geneva",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A meeting cannot be locked from the inside and a template at the same time.",
            response.json["message"],
        )

    def test_update_cant_lock_template_2(self) -> None:
        self.create_meeting()
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {
                    "template_for_organization_id": 1,
                    "locked_from_inside": True,
                    "admin_group_id": 2,
                }
            }
        )
        self.set_user_groups(1, [2])
        response = self.request(
            "meeting.update",
            {"id": 1, "location": "Geneva"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A meeting cannot be locked from the inside and a template at the same time.",
            response.json["message"],
        )

    def test_update_cant_lock_template_3(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {
                    "template_for_organization_id": 1,
                }
            }
        )
        response = self.request(
            "meeting.update",
            {"id": 1, "locked_from_inside": True, "location": "Geneva"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A meeting cannot be locked from the inside and a template at the same time.",
            response.json["message"],
        )

    def test_update_cant_lock_template_4(self) -> None:
        self.create_meeting()
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {
                    "locked_from_inside": True,
                    "admin_group_id": 2,
                }
            }
        )
        self.set_user_groups(1, [2])
        response = self.request(
            "meeting.update",
            {"id": 1, "set_as_template": True, "location": "Geneva"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A meeting cannot be locked from the inside and a template at the same time.",
            response.json["message"],
        )

    def test_update_cant_lock_public_meeting(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "enable_anonymous": True,
                "locked_from_inside": True,
                "location": "Geneva",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A meeting cannot be locked from the inside and have anonymous enabled at the same time.",
            response.json["message"],
        )

    def test_update_cant_lock_public_meeting_2(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {
                    "enable_anonymous": True,
                }
            }
        )
        response = self.request(
            "meeting.update",
            {"id": 1, "locked_from_inside": True, "location": "Geneva"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A meeting cannot be locked from the inside and have anonymous enabled at the same time.",
            response.json["message"],
        )

    def test_update_cant_lock_public_meeting_3(self) -> None:
        self.create_meeting()
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {
                    "locked_from_inside": True,
                    "admin_group_id": 2,
                }
            }
        )
        self.set_user_groups(1, [2])
        response = self.request(
            "meeting.update",
            {"id": 1, "enable_anonymous": True, "location": "Geneva"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A meeting cannot be locked from the inside and have anonymous enabled at the same time.",
            response.json["message"],
        )

    def test_update_set_anonymous_with_anonymous_group_already_existing(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "meeting/1": {"anonymous_group_id": 99, "group_ids": [1, 99]},
                "group/99": {
                    "anonymous_group_for_meeting_id": 1,
                    "name": "Anonymous",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "enable_anonymous": True,
                "location": "Geneva",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("group/100")

    def base_anonymous_group_in_poll_default_field_test(self, field: str) -> None:
        self.create_meeting()
        self.set_anonymous()
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                field: [4],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            f"Anonymous group is not allowed in {field}.",
            response.json["message"],
        )

    def test_anonymous_in_assignment_poll_default_group_ids(self) -> None:
        self.base_anonymous_group_in_poll_default_field_test(
            "assignment_poll_default_group_ids"
        )

    def test_anonymous_in_motion_poll_default_group_ids(self) -> None:
        self.base_anonymous_group_in_poll_default_field_test(
            "motion_poll_default_group_ids"
        )

    def test_anonymous_in_topic_poll_default_group_ids(self) -> None:
        self.base_anonymous_group_in_poll_default_field_test(
            "topic_poll_default_group_ids"
        )

    def test_update_enable_anonymous_check_language(self) -> None:
        self.test_models["meeting/1"]["language"] = "de"
        self.set_models(self.test_models)
        response = self.request(
            "meeting.update",
            {
                "id": 1,
                "enable_anonymous": True,
            },
        )
        self.assert_status_code(response, 200)
        Translator.set_translation_language("de")
        self.assert_model_exists("group/2", {"name": _("Public")})
