from typing import Any, Dict
from unittest.mock import MagicMock

from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.management_levels import CommitteeManagementLevel
from tests.system.action.base import BaseActionTestCase


class MeetingClone(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: Dict[str, Dict[str, Any]] = {
            "organization/1": {"active_meeting_ids": [1], "organization_tag_ids": [1]},
            "organization_tag/1": {
                "name": "TEST",
                "color": "#eeeeee",
                "organization_id": 1,
            },
            "committee/1": {"organization_id": 1},
            "meeting/1": {
                "committee_id": 1,
                "name": "Test",
                "admin_group_id": 1,
                "default_group_id": 1,
                "motions_default_amendment_workflow_id": 1,
                "motions_default_statute_amendment_workflow_id": 1,
                "motions_default_workflow_id": 1,
                "reference_projector_id": 1,
                "projector_countdown_default_time": 60,
                "projector_countdown_warning_time": 5,
                "projector_ids": [1],
                "group_ids": [1],
                "motion_state_ids": [1],
                "motion_workflow_ids": [1],
                "logo_$_id": None,
                "font_$_id": [],
                "default_projector_$_id": None,
                "is_active_in_organization_id": 1,
            },
            "group/1": {
                "meeting_id": 1,
                "name": "testgroup",
                "admin_group_for_meeting_id": 1,
                "default_group_for_meeting_id": 1,
            },
            "motion_workflow/1": {
                "meeting_id": 1,
                "name": "blup",
                "first_state_id": 1,
                "default_amendment_workflow_meeting_id": 1,
                "default_statute_amendment_workflow_meeting_id": 1,
                "default_workflow_meeting_id": 1,
                "state_ids": [1],
            },
            "motion_state/1": {
                "css_class": "lightblue",
                "meeting_id": 1,
                "workflow_id": 1,
                "name": "test",
                "weight": 1,
                "workflow_id": 1,
                "first_state_of_workflow_id": 1,
            },
            "projector/1": {
                "meeting_id": 1,
                "used_as_reference_projector_meeting_id": 1,
                "name": "Default projector",
                "used_as_default_$_in_meeting_id": [],
            },
        }

    def test_clone_without_users(self) -> None:
        self.set_models(self.test_models)

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 1,
                "name": "Test - Copy",
                "admin_group_id": 2,
                "default_group_id": 2,
                "motions_default_amendment_workflow_id": 2,
                "motions_default_statute_amendment_workflow_id": 2,
                "motions_default_workflow_id": 2,
                "reference_projector_id": 2,
                "projector_countdown_default_time": 60,
                "projector_countdown_warning_time": 5,
                "projector_ids": [2],
                "group_ids": [2],
                "motion_state_ids": [2],
                "motion_workflow_ids": [2],
                "logo_$_id": None,
                "font_$_id": [],
                "default_projector_$_id": None,
            },
        )

    def test_clone_with_users(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["group/1"]["user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "meeting_ids": [1],
                }
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "group_$_ids": ["1", "2"],
                "group_$1_ids": [1],
                "group_$2_ids": [2],
                "meeting_ids": [1, 2],
            },
        )
        self.assert_model_exists("meeting/1", {"user_ids": [1]})
        self.assert_model_exists("meeting/2", {"user_ids": [1]})

    def test_clone_with_set_fields(self) -> None:
        self.set_models(self.test_models)

        response = self.request(
            "meeting.clone",
            {
                "meeting_id": 1,
                "welcome_title": "Modifizierte Name",
                "description": "blablabla",
                "start_time": 1641370959,
                "end_time": 1641370959,
                "location": "Testraum",
                "organization_tag_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "welcome_title": "Modifizierte Name",
                "description": "blablabla",
                "location": "Testraum",
                "organization_tag_ids": [1],
                "start_time": 1641370959,
                "end_time": 1641370959,
            },
        )

    def test_clone_with_personal_note(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["personal_note_ids"] = [1]
        self.test_models["group/1"]["user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "personal_note_$_ids": ["1"],
                    "personal_note_$1_ids": [1],
                },
                "personal_note/1": {
                    "note": "test note",
                    "user_id": 1,
                    "meeting_id": 1,
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "personal_note_$_ids": ["1", "2"],
                "personal_note_$1_ids": [1],
                "personal_note_$2_ids": [2],
            },
        )

    def test_clone_with_option(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["option_ids"] = [1]
        self.test_models["group/1"]["user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "option_$_ids": ["1"],
                    "option_$1_ids": [1],
                },
                "option/1": {"content_object_id": "user/1", "meeting_id": 1},
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "option_$_ids": ["1", "2"],
                "option_$1_ids": [1],
                "option_$2_ids": [2],
            },
        )

    def test_clone_with_mediafile(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["meeting/1"]["mediafile_ids"] = [1]
        self.test_models["group/1"]["user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "meeting_ids": [1],
                },
                "mediafile/1": {
                    "meeting_id": 1,
                    "attachment_ids": [],
                    "used_as_font_$_in_meeting_id": [],
                    "used_as_logo_$_in_meeting_id": [],
                    "mimetype": "text/plain",
                    "is_public": True,
                },
            }
        )
        self.set_models(self.test_models)
        self.media.duplicate_mediafile = MagicMock()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.media.duplicate_mediafile.assert_called_with(1, 2)

    def test_clone_with_mediafile_directory(self) -> None:
        self.test_models["meeting/1"]["user_ids"] = [1]
        self.test_models["group/1"]["user_ids"] = [1]
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "meeting_ids": [1],
                },
            }
        )
        self.set_models(self.test_models)
        response = self.request(
            "mediafile.create_directory", {"meeting_id": 1, "title": "bla"}
        )
        self.assert_status_code(response, 200)

        self.media.duplicate_mediafile = MagicMock()
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_with_organization_tag(self) -> None:
        self.test_models["meeting/1"]["organization_tag_ids"] = [1]
        self.set_models(
            {
                "organization_tag/1": {
                    "name": "Test",
                    "color": "#ffffff",
                    "tagged_ids": ["meeting/1"],
                }
            }
        )
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"organization_tag_ids": [1]})

    def test_clone_with_settings(self) -> None:
        self.set_models(self.test_models)
        settings = {
            "welcome_title": "title",
            "welcome_text": "text",
            "name": "name",
            "description": "desc",
            "location": "loc",
            "start_time": 1633522986,
            "end_time": 1633522986,
            "conference_show": True,
            "conference_auto_connect": True,
            "conference_los_restriction": True,
            "conference_stream_url": "url",
            "conference_stream_poster_url": "url",
            "conference_open_microphone": True,
            "conference_open_video": True,
            "conference_auto_connect_next_speakers": 42,
            "conference_enable_helpdesk": True,
            "applause_enable": True,
            "applause_type": "applause-type-particles",
            "applause_show_level": True,
            "applause_min_amount": 42,
            "applause_max_amount": 42,
            "applause_timeout": 42,
            "applause_particle_image_url": "url",
            "projector_countdown_default_time": 42,
            "projector_countdown_warning_time": 42,
            "export_csv_encoding": "iso-8859-15",
            "export_csv_separator": ";",
            "export_pdf_pagenumber_alignment": "left",
            "export_pdf_fontsize": 12,
            "export_pdf_pagesize": "A5",
            "agenda_show_subtitles": True,
            "agenda_enable_numbering": False,
            "agenda_number_prefix": "prefix",
            "agenda_numeral_system": "roman",
            "agenda_item_creation": "always",
            "agenda_new_items_default_visibility": "common",
            "agenda_show_internal_items_on_projector": False,
            "list_of_speakers_amount_last_on_projector": 42,
            "list_of_speakers_amount_next_on_projector": 42,
            "list_of_speakers_couple_countdown": False,
            "list_of_speakers_show_amount_of_speakers_on_slide": False,
            "list_of_speakers_present_users_only": True,
            "list_of_speakers_show_first_contribution": True,
            "list_of_speakers_enable_point_of_order_speakers": True,
            "list_of_speakers_enable_pro_contra_speech": True,
            "list_of_speakers_can_set_contribution_self": True,
            "list_of_speakers_speaker_note_for_everyone": True,
            "list_of_speakers_initially_closed": True,
            "motions_preamble": "preamble",
            "motions_default_line_numbering": "inline",
            "motions_line_length": 42,
            "motions_reason_required": True,
            "motions_enable_text_on_projector": True,
            "motions_enable_reason_on_projector": True,
            "motions_enable_sidebox_on_projector": True,
            "motions_enable_recommendation_on_projector": True,
            "motions_show_referring_motions": True,
            "motions_show_sequential_number": True,
            "motions_recommendations_by": "rec",
            "motions_statute_recommendations_by": "rec",
            "motions_recommendation_text_mode": "original",
            "motions_default_sorting": "weight",
            "motions_number_type": "manually",
            "motions_number_min_digits": 42,
            "motions_number_with_blank": True,
            "motions_statutes_enabled": True,
            "motions_amendments_enabled": True,
            "motions_amendments_in_main_list": True,
            "motions_amendments_of_amendments": True,
            "motions_amendments_prefix": "prefix",
            "motions_amendments_text_mode": "freestyle",
            "motions_amendments_multiple_paragraphs": True,
            "motions_supporters_min_amount": 42,
            "motions_export_title": "title",
            "motions_export_preamble": "pre",
            "motions_export_submitter_recommendation": True,
            "motions_export_follow_recommendation": True,
            "motion_poll_ballot_paper_selection": "NUMBER_OF_DELEGATES",
            "motion_poll_ballot_paper_number": 42,
            "motion_poll_default_type": "pseudoanonymous",
            "motion_poll_default_100_percent_base": "YN",
            "users_sort_by": "number",
            "users_enable_presence_view": True,
            "users_enable_vote_weight": True,
            "users_allow_self_set_present": True,
            "users_pdf_welcometitle": "title",
            "users_pdf_welcometext": "text",
            "users_pdf_url": "url",
            "users_pdf_wlan_ssid": "wifi",
            "users_pdf_wlan_password": "pw",
            "users_pdf_wlan_encryption": "WEP",
            "users_email_sender": "sender",
            "users_email_replyto": "replyto",
            "users_email_subject": "subject",
            "users_email_body": "body",
            "assignments_export_title": "title",
            "assignments_export_preamble": "pre",
            "assignment_poll_ballot_paper_selection": "NUMBER_OF_DELEGATES",
            "assignment_poll_ballot_paper_number": 42,
            "assignment_poll_add_candidates_to_list_of_speakers": True,
            "assignment_poll_sort_poll_result_by_votes": True,
            "assignment_poll_default_type": "pseudoanonymous",
            "assignment_poll_default_method": "YNA",
            "assignment_poll_default_100_percent_base": "YNA",
        }
        self.update_model("meeting/1", settings)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        settings["name"] += " - Copy"  # type: ignore
        self.assert_model_exists("meeting/2", settings)

    def test_limit_of_meetings_error(self) -> None:
        self.test_models["organization/1"]["limit_of_meetings"] = 1
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "You cannot clone an meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )

    def test_limit_of_meetings_error_archived_meeting(self) -> None:
        self.test_models["organization/1"]["limit_of_meetings"] = 1
        self.test_models["organization/1"]["active_meeting_ids"] = [3]
        self.test_models["meeting/1"]["is_active_in_organization_id"] = None
        self.set_models(self.test_models)

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "You cannot clone an meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )

    def test_activate_archived_meeting(self) -> None:
        self.test_models["organization/1"]["limit_of_meetings"] = 2
        self.test_models["organization/1"]["active_meeting_ids"] = [3]
        self.test_models["meeting/1"]["is_active_in_organization_id"] = None
        self.set_models(self.test_models)

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"is_active_in_organization_id": 1})
        self.assert_model_exists("organization/1", {"active_meeting_ids": [3, 2]})

    def test_limit_of_meetings_ok(self) -> None:
        self.test_models["organization/1"]["limit_of_meetings"] = 2
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        organization = self.get_model("organization/1")
        self.assertCountEqual(organization["active_meeting_ids"], [1, 2])

    def test_create_clone(self) -> None:
        self.set_models(
            {
                "organization/1": {},
                "committee/1": {"organization_id": 1, "user_ids": [2, 3]},
                "user/2": {"committee_ids": [1]},
                "user/3": {"committee_ids": [1]},
            }
        )
        response = self.request(
            "meeting.create",
            {
                "committee_id": 1,
                "name": "meeting",
                "description": "",
                "location": "",
                "start_time": 1633039200,
                "end_time": 1633039200,
                "user_ids": [2, 3],
                "admin_ids": [],
                "organization_tag_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_meeting_name_too_long(self) -> None:
        long_name = "0123456789" * 10
        self.test_models["meeting/1"]["name"] = long_name
        self.set_models(self.test_models)
        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"name": long_name + " - Copy"})

    def test_permissions_both_okay(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$2_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_ids": [1, 2],
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 1}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 2}
        )

    def test_permissions_oml_can_manage(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "organization_management_level": "can_manage_organization",
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"is_active_in_organization_id": 1, "committee_id": 1}
        )
        self.assert_model_exists(
            "meeting/2", {"is_active_in_organization_id": 1, "committee_id": 2}
        )

    def test_permissions_missing_meeting_committee_permission(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "committee_$2_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_ids": [2],
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 403)
        self.assertIn(
            "Missing CommitteeManagementLevel: can_manage for committee 1",
            response.json["message"],
        )

    def test_permissions_missing_payload_committee_permission(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/2": {"organization_id": 1},
                "user/1": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_ids": [1],
                    "organization_management_level": None,
                },
            }
        )
        response = self.request("meeting.clone", {"meeting_id": 1, "committee_id": 2})
        self.assert_status_code(response, 403)
        self.assertIn(
            "Missing CommitteeManagementLevel: can_manage for committee 2",
            response.json["message"],
        )

    def test_clone_with_created_topic_and_agenda_type(self) -> None:
        self.set_models(self.test_models)

        response = self.request(
            "topic.create",
            {
                "meeting_id": 1,
                "title": "test",
                "agenda_type": AgendaItem.INTERNAL_ITEM,
                "agenda_duration": 60,
            },
        )
        self.assert_status_code(response, 200)
        topic_fqid = f'topic/{response.json["results"][0][0]["id"]}'
        topic = self.get_model(topic_fqid)
        self.assertNotIn("agenda_type", topic)
        self.assertNotIn("agenda_duration", topic)
        agenda_item_fqid = f"agenda_item/{topic.get('agenda_item_id')}"
        self.assert_model_exists(
            agenda_item_fqid,
            {
                "type": AgendaItem.INTERNAL_ITEM,
                "duration": 60,
                "content_object_id": topic_fqid,
            },
        )

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_with_created_motion_and_agenda_type(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "motion.create",
            {
                "meeting_id": 1,
                "title": "test",
                "text": "Motion test",
                "agenda_create": False,
                "agenda_type": AgendaItem.INTERNAL_ITEM,
                "agenda_duration": 60,
            },
        )
        self.assert_status_code(response, 200)
        motion_fqid = f'motion/{response.json["results"][0][0]["id"]}'
        self.assert_model_exists(
            motion_fqid,
            {
                "agenda_item_id": None,
                "agenda_create": None,
                "agenda_type": None,
                "agenda_duration": None,
            },
        )

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_clone_with_archived_meeting(self) -> None:
        """
        Archived meeting stays archived by cloning
        """
        self.test_models["meeting/1"]["is_active_in_organization_id"] = None
        self.set_models(self.test_models)

        response = self.request("meeting.clone", {"meeting_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"is_active_in_organization_id": None})
