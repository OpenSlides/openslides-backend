import time
from typing import Any, Dict

from tests.system.action.base import BaseActionTestCase


class MeetingImport(BaseActionTestCase):
    def create_request_data(self, datapart: Dict[str, Any]) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "committee_id": 1,
            "meeting": {
                "meeting": [
                    {
                        "id": 1,
                        "name": "Test",
                        "description": "blablabla",
                        "admin_group_id": 1,
                        "default_group_id": 1,
                        "motions_default_amendment_workflow_id": 1,
                        "motions_default_statute_amendment_workflow_id": 1,
                        "motions_default_workflow_id": 1,
                        "projector_countdown_default_time": 60,
                        "projector_countdown_warning_time": 60,
                        "reference_projector_id": 1,
                        "user_ids": [1],
                        "imported_at": None,
                        "custom_translations": None,
                        "url_name": "os3_test",
                        "template_for_committee_id": None,
                        "enable_anonymous": False,
                        "location": "",
                        "start_time": 10,
                        "end_time": 10,
                        "welcome_title": "Welcome to OpenSlides",
                        "welcome_text": "[Space for your welcome text.]",
                        "conference_show": False,
                        "conference_auto_connect": False,
                        "conference_los_restriction": False,
                        "conference_stream_url": "",
                        "conference_stream_poster_url": "",
                        "conference_open_microphone": True,
                        "conference_open_video": True,
                        "conference_auto_connect_next_speakers": 1,
                        "jitsi_room_name": "",
                        "jitsi_domain": "",
                        "jitsi_room_password": "",
                        "enable_chat": True,
                        "export_csv_encoding": "utf-8",
                        "export_csv_separator": ",",
                        "export_pdf_pagenumber_alignment": "center",
                        "export_pdf_fontsize": 10,
                        "export_pdf_pagesize": "A4",
                        "agenda_show_subtitles": False,
                        "agenda_enable_numbering": True,
                        "agenda_number_prefix": "",
                        "agenda_numeral_system": "arabic",
                        "agenda_item_creation": "default_yes",
                        "agenda_new_items_default_visibility": "internal",
                        "agenda_show_internal_items_on_projector": False,
                        "list_of_speakers_amount_last_on_projector": 1,
                        "list_of_speakers_amount_next_on_projector": 1,
                        "list_of_speakers_couple_countdown": True,
                        "list_of_speakers_show_amount_of_speakers_on_slide": True,
                        "list_of_speakers_present_users_only": False,
                        "list_of_speakers_show_first_contribution": False,
                        "list_of_speakers_enable_point_of_order_speakers": True,
                        "list_of_speakers_enable_pro_contra_speech": True,
                        "list_of_speakers_can_set_contribution_self": True,
                        "list_of_speakers_speaker_note_for_everyone": True,
                        "list_of_speakers_initially_closed": True,
                        "motions_preamble": "The assembly may decide:",
                        "motions_default_line_numbering": "none",
                        "motions_line_length": 90,
                        "motions_reason_required": False,
                        "motions_enable_text_on_projector": True,
                        "motions_enable_reason_on_projector": True,
                        "motions_enable_sidebox_on_projector": True,
                        "motions_enable_recommendation_on_projector": True,
                        "motions_show_referring_motions": True,
                        "motions_show_sequential_number": True,
                        "motions_recommendations_by": "ABK",
                        "motions_statute_recommendations_by": "Statute ABK",
                        "motions_recommendation_text_mode": "original",
                        "motions_default_sorting": "number",
                        "motions_number_type": "per_category",
                        "motions_number_min_digits": 3,
                        "motions_number_with_blank": False,
                        "motions_statutes_enabled": True,
                        "motions_amendments_enabled": True,
                        "motions_amendments_in_main_list": True,
                        "motions_amendments_of_amendments": True,
                        "motions_amendments_prefix": "Ä-",
                        "motions_amendments_text_mode": "freestyle",
                        "motions_amendments_multiple_paragraphs": True,
                        "motions_supporters_min_amount": 1,
                        "motions_export_title": "Motions",
                        "motions_export_preamble": "an export preamble",
                        "motions_export_submitter_recommendation": True,
                        "motions_export_follow_recommendation": True,
                        "motion_poll_ballot_paper_selection": "CUSTOM_NUMBER",
                        "motion_poll_ballot_paper_number": 8,
                        "motion_poll_default_type": "analog",
                        "motion_poll_default_100_percent_base": "YNA",
                        "motion_poll_default_majority_method": "simple",
                        "motion_poll_default_group_ids": [],
                        "users_sort_by": "first_name",
                        "users_enable_presence_view": True,
                        "users_enable_vote_weight": True,
                        "users_allow_self_set_present": True,
                        "users_pdf_welcometitle": "Welcome to OpenSlides",
                        "users_pdf_welcometext": "[Place for your welcome and help text.]",
                        "users_pdf_url": "http://example.com:8000",
                        "users_pdf_wlan_ssid": "",
                        "users_pdf_wlan_password": "",
                        "users_pdf_wlan_encryption": "",
                        "users_email_sender": "noreply@yourdomain.com",
                        "users_email_replyto": "",
                        "users_email_subject": "Your login for {event_name}",
                        "users_email_body": "Dear {name},\n\nthis is your OpenSlides login for the event {event_name}:\n\n    {url}\n    username: {username}\n    password: {password}\n\nThis email was generated automatically.",
                        "assignments_export_title": "Elections",
                        "assignments_export_preamble": "",
                        "assignment_poll_ballot_paper_selection": "CUSTOM_NUMBER",
                        "assignment_poll_ballot_paper_number": 8,
                        "assignment_poll_add_candidates_to_list_of_speakers": True,
                        "assignment_poll_sort_poll_result_by_votes": True,
                        "assignment_poll_default_type": "nominal",
                        "assignment_poll_default_method": "votes",
                        "assignment_poll_default_100_percent_base": "valid",
                        "assignment_poll_default_majority_method": "simple",
                        "assignment_poll_default_group_ids": [],
                        "poll_ballot_paper_selection": "CUSTOM_NUMBER",
                        "poll_ballot_paper_number": 8,
                        "poll_sort_poll_result_by_votes": True,
                        "poll_default_type": "nominal",
                        "poll_default_method": "votes",
                        "poll_default_100_percent_base": "valid",
                        "poll_default_majority_method": "simple",
                        "poll_default_group_ids": [],
                        "poll_couple_countdown": True,
                        "projector_ids": [1],
                        "all_projection_ids": [],
                        "projector_message_ids": [],
                        "projector_countdown_ids": [],
                        "tag_ids": [],
                        "agenda_item_ids": [],
                        "list_of_speakers_ids": [],
                        "speaker_ids": [],
                        "topic_ids": [],
                        "group_ids": [1],
                        "mediafile_ids": [],
                        "motion_ids": [],
                        "motion_submitter_ids": [],
                        "motion_comment_section_ids": [],
                        "motion_comment_ids": [],
                        "motion_state_ids": [1],
                        "motion_category_ids": [],
                        "motion_block_ids": [],
                        "motion_workflow_ids": [1],
                        "motion_statute_paragraph_ids": [],
                        "motion_change_recommendation_ids": [],
                        "poll_ids": [],
                        "option_ids": [],
                        "vote_ids": [],
                        "assignment_ids": [],
                        "assignment_candidate_ids": [],
                        "personal_note_ids": [],
                        "chat_group_ids": [],
                        "logo_$_id": [],
                        "font_$_id": [],
                        "committee_id": None,
                        "default_meeting_for_committee_id": None,
                        "organization_tag_ids": [],
                        "present_user_ids": [],
                        "list_of_speakers_countdown_id": None,
                        "poll_countdown_id": None,
                        "default_projector_$_id": [],
                        "projection_ids": [],
                    }
                ],
                "user": [
                    {
                        "id": 1,
                        "password": "",
                        "username": "test",
                        "group_$_ids": ["1"],
                        "group_$1_ids": [1],
                        "committee_ids": [],
                        "committee_$_management_level": [],
                        "vote_weight_$": [],
                        "id": 1,
                        "title": "",
                        "first_name": "",
                        "last_name": "Administrator",
                        "is_active": True,
                        "is_physical_person": True,
                        "default_password": "admin",
                        "can_change_own_password": True,
                        "gender": "",
                        "email": "",
                        "default_number": "",
                        "default_structure_level": "",
                        "default_vote_weight": "1.000000",
                        "last_email_send": None,
                        "is_demo_user": False,
                        "organization_management_level": "superadmin",
                        "is_present_in_meeting_ids": [],
                        "comment_$": [],
                        "number_$": [],
                        "structure_level_$": [],
                        "about_me_$": [],
                        "speaker_$_ids": [],
                        "personal_note_$_ids": [],
                        "supported_motion_$_ids": [],
                        "submitted_motion_$_ids": [],
                        "assignment_candidate_$_ids": [],
                        "poll_voted_$_ids": [],
                        "option_$_ids": [],
                        "vote_$_ids": [],
                        "projection_$_ids": [],
                        "vote_delegated_vote_$_ids": [],
                        "vote_delegated_$_to_id": [],
                        "vote_delegations_$_from_ids": [],
                        "meeting_ids": [1],
                    }
                ],
                "group": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "name": "testgroup",
                        "user_ids": [1],
                        "admin_group_for_meeting_id": 1,
                        "default_group_for_meeting_id": 1,
                        "permissions": [],
                        "mediafile_access_group_ids": [],
                        "mediafile_inherited_access_group_ids": [],
                        "read_comment_section_ids": [],
                        "write_comment_section_ids": [],
                        "read_chat_group_ids": [],
                        "write_chat_group_ids": [],
                        "poll_ids": [],
                        "used_as_motion_poll_default_id": None,
                        "used_as_assignment_poll_default_id": None,
                        "used_as_poll_default_id": None,
                    }
                ],
                "motion_workflow": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "name": "blup",
                        "first_state_id": 1,
                        "default_amendment_workflow_meeting_id": 1,
                        "default_statute_amendment_workflow_meeting_id": 1,
                        "default_workflow_meeting_id": 1,
                        "state_ids": [1],
                    }
                ],
                "motion_state": [
                    {
                        "id": 1,
                        "css_class": "lightblue",
                        "meeting_id": 1,
                        "workflow_id": 1,
                        "name": "test",
                        "recommendation_label": None,
                        "restrictions": [],
                        "allow_support": True,
                        "allow_create_poll": True,
                        "allow_submitter_edit": True,
                        "set_number": True,
                        "show_state_extension_field": False,
                        "merge_amendment_into_final": "undefined",
                        "show_recommendation_extension_field": False,
                        "next_state_ids": [],
                        "previous_state_ids": [],
                        "motion_ids": [],
                        "motion_recommendation_ids": [],
                        "workflow_id": 1,
                        "first_state_of_workflow_id": 1,
                    }
                ],
                "projector": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "used_as_reference_projector_meeting_id": 1,
                        "name": "Default projector",
                        "scale": 10,
                        "scroll": 10,
                        "width": 1220,
                        "aspect_ratio_numerator": 4,
                        "aspect_ratio_denominator": 3,
                        "color": "#000000",
                        "background_color": "#ffffff",
                        "header_background_color": "#317796",
                        "header_font_color": "#f5f5f5",
                        "header_h1_color": "#317796",
                        "chyron_background_color": "#317796",
                        "chyron_font_color": "#ffffff",
                        "show_header_footer": True,
                        "show_title": True,
                        "show_logo": True,
                        "show_clock": True,
                        "current_projection_ids": [],
                        "preview_projection_ids": [],
                        "history_projection_ids": [],
                        "used_as_default_$_in_meeting_id": [],
                    }
                ],
                **datapart,
            },
        }
        needed_collections = (
            "user",
            "meeting",
            "group",
            "personal_note",
            "tag",
            "agenda_item",
            "list_of_speakers",
            "speaker",
            "topic",
            "motion",
            "motion_submitter",
            "motion_comment",
            "motion_comment_section",
            "motion_category",
            "motion_block",
            "motion_change_recommendation",
            "motion_state",
            "motion_workflow",
            "motion_statute_paragraph",
            "poll",
            "option",
            "vote",
            "assignment",
            "assignment_candidate",
            "mediafile",
            "projector",
            "projection",
            "projector_message",
            "projector_countdown",
            "chat_group",
        )
        for collection in needed_collections:
            if collection not in data["meeting"]:
                data["meeting"][collection] = []

        return data

    def test_no_meeting_collection(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "meeting.import", {"committee_id": 1, "meeting": {"meeting": []}}
        )
        self.assert_status_code(response, 400)
        assert (
            "Need exact one meeting in meeting collection." in response.json["message"]
        )

    def test_too_many_meeting_collections(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "meeting.import",
            {"committee_id": 1, "meeting": {"meeting": [{"id": 1}, {"id": 2}]}},
        )
        self.assert_status_code(response, 400)
        assert (
            "Need exact one meeting in meeting collection." in response.json["message"]
        )

    def test_include_organization(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        request_data = self.create_request_data({"organization": [{"id": 1}]})

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert "Invalid collections: organization." in response.json["message"]

    def test_replace_ids_and_write_to_datastore(self) -> None:
        start = round(time.time())
        self.set_models(
            {
                "committee/1": {"meeting_ids": []},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        request_data = self.create_request_data(
            {
                "personal_note": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "note": "<p>Some content..</p>",
                        "star": False,
                        "user_id": 1,
                    }
                ],
                "motion": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "list_of_speakers_id": 1,
                        "state_id": 1,
                        "title": "bla",
                        "number": "1 - 1",
                        "number_value": 1,
                        "sequential_number": 2,
                        "text": "<p>l&ouml;mk</p>",
                        "amendment_paragraph_$": [],
                        "modified_final_version": "",
                        "reason": "",
                        "category_weight": 10000,
                        "state_extension": "<p>regeer</p>",
                        "recommendation_extension": None,
                        "sort_weight": 10000,
                        "created": 1584512346,
                        "last_modified": 1584512346,
                        "lead_motion_id": None,
                        "amendment_ids": [],
                        "sort_parent_id": None,
                        "sort_child_ids": [],
                        "origin_id": None,
                        "derived_motion_ids": [],
                        "forwarding_tree_motion_ids": [],
                        "recommendation_id": None,
                        "recommendation_extension_reference_ids": [],
                        "referenced_in_motion_recommendation_extension_ids": [],
                        "category_id": None,
                        "block_id": None,
                        "submitter_ids": [],
                        "supporter_ids": [],
                        "poll_ids": [],
                        "option_ids": [],
                        "change_recommendation_ids": [],
                        "statute_paragraph_id": None,
                        "comment_ids": [],
                        "agenda_item_id": None,
                        "tag_ids": [1],
                        "attachment_ids": [],
                        "projection_ids": [],
                        "personal_note_ids": [1],
                    }
                ],
                "list_of_speakers": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "speaker_ids": [],
                        "projection_ids": [],
                    }
                ],
                "tag": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "tagged_ids": ["motion/1"],
                        "name": "testag",
                    }
                ],
            }
        )
        request_data["meeting"]["meeting"][0]["personal_note_ids"] = [1]
        request_data["meeting"]["user"][0]["personal_note_$_ids"] = ["1"]
        request_data["meeting"]["user"][0]["personal_note_$1_ids"] = [1]
        request_data["meeting"]["meeting"][0]["motion_ids"] = [1]
        request_data["meeting"]["motion_state"][0]["motion_ids"] = [1]
        request_data["meeting"]["meeting"][0]["list_of_speakers_ids"] = [1]
        request_data["meeting"]["meeting"][0]["tag_ids"] = [1]

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "name": "Test",
                "description": "blablabla",
                "committee_id": 1,
                "enable_anonymous": False,
            },
        )
        meeting_2 = self.get_model("meeting/2")
        assert start <= meeting_2.get("imported_at", 0) <= start + 300
        self.assert_model_exists(
            "user/2", {"username": "test", "group_$2_ids": [1], "group_$_ids": ["2"]}
        )
        user_2 = self.get_model("user/2")
        assert user_2.get("password", "")
        self.assert_model_exists("projector/1", {"meeting_id": 2})
        self.assert_model_exists("group/1", {"user_ids": [1, 2]})
        self.assert_model_exists("personal_note/1", {"content_object_id": "motion/2"})
        self.assert_model_exists(
            "tag/1", {"tagged_ids": ["motion/2"], "name": "testag"}
        )
        self.assert_model_exists("committee/1", {"meeting_ids": [2]})

    def test_check_usernames(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
                "user/1": {"username": "admin"},
            }
        )
        request_data = self.create_request_data({})
        request_data["meeting"]["user"] = [
            {
                "id": 1,
                "password": "",
                "username": "admin",
                "group_$_ids": ["1"],
                "group_$1_ids": [1],
                "committee_ids": [],
                "committee_$_management_level": [],
                "vote_weight_$": [],
                "id": 1,
                "title": "",
                "first_name": "",
                "last_name": "Administrator",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "admin",
                "can_change_own_password": True,
                "gender": "",
                "email": "",
                "default_number": "",
                "default_structure_level": "",
                "default_vote_weight": "1.000000",
                "last_email_send": None,
                "is_demo_user": False,
                "organization_management_level": "superadmin",
                "is_present_in_meeting_ids": [],
                "comment_$": [],
                "number_$": [],
                "structure_level_$": [],
                "about_me_$": [],
                "speaker_$_ids": [],
                "personal_note_$_ids": [],
                "supported_motion_$_ids": [],
                "submitted_motion_$_ids": [],
                "assignment_candidate_$_ids": [],
                "poll_voted_$_ids": [],
                "option_$_ids": [],
                "vote_$_ids": [],
                "projection_$_ids": [],
                "vote_delegated_vote_$_ids": [],
                "vote_delegated_$_to_id": [],
                "vote_delegations_$_from_ids": [],
                "meeting_ids": [1],
            }
        ]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "admin 1"})

    def test_check_usernames_2(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
                "user/1": {"username": "admin"},
            }
        )
        request_data = self.create_request_data({})
        request_data["meeting"]["user"] = [
            {
                "id": 1,
                "password": "",
                "username": "admin",
                "group_$_ids": ["1"],
                "group_$1_ids": [1],
                "committee_ids": [],
                "committee_$_management_level": [],
                "vote_weight_$": [],
                "id": 1,
                "title": "",
                "first_name": "",
                "last_name": "Administrator",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "admin",
                "can_change_own_password": True,
                "gender": "",
                "email": "",
                "default_number": "",
                "default_structure_level": "",
                "default_vote_weight": "1.000000",
                "last_email_send": None,
                "is_demo_user": False,
                "organization_management_level": "superadmin",
                "is_present_in_meeting_ids": [],
                "comment_$": [],
                "number_$": [],
                "structure_level_$": [],
                "about_me_$": [],
                "speaker_$_ids": [],
                "personal_note_$_ids": [],
                "supported_motion_$_ids": [],
                "submitted_motion_$_ids": [],
                "assignment_candidate_$_ids": [],
                "poll_voted_$_ids": [],
                "option_$_ids": [],
                "vote_$_ids": [],
                "projection_$_ids": [],
                "vote_delegated_vote_$_ids": [],
                "vote_delegated_$_to_id": [],
                "vote_delegations_$_from_ids": [],
                "meeting_ids": [1],
            },
            {
                "id": 2,
                "password": "",
                "username": "admin 1",
                "group_$_ids": [],
                "committee_ids": [],
                "committee_$_management_level": [],
                "vote_weight_$": [],
                "title": "",
                "first_name": "",
                "last_name": "Administrator",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "admin",
                "can_change_own_password": True,
                "gender": "",
                "email": "",
                "default_number": "",
                "default_structure_level": "",
                "default_vote_weight": "1.000000",
                "last_email_send": None,
                "is_demo_user": False,
                "organization_management_level": "superadmin",
                "is_present_in_meeting_ids": [],
                "comment_$": [],
                "number_$": [],
                "structure_level_$": [],
                "about_me_$": [],
                "speaker_$_ids": [],
                "personal_note_$_ids": [],
                "supported_motion_$_ids": [],
                "submitted_motion_$_ids": [],
                "assignment_candidate_$_ids": [],
                "poll_voted_$_ids": [],
                "option_$_ids": [],
                "vote_$_ids": [],
                "projection_$_ids": [],
                "vote_delegated_vote_$_ids": [],
                "vote_delegated_$_to_id": [],
                "vote_delegations_$_from_ids": [],
                "meeting_ids": [1],
            },
        ]

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "admin 1"})
        self.assert_model_exists("user/3", {"username": "admin 1 1"})

    def test_double_import(self) -> None:
        start = round(time.time())
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
                "user/1": {"username": "admin"},
            }
        )
        request_data = self.create_request_data(
            {
                "personal_note": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "note": "<p>Some content..</p>",
                        "star": False,
                        "user_id": 1,
                    }
                ],
                "motion": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "list_of_speakers_id": 1,
                        "state_id": 1,
                        "title": "bla",
                        "number": "1 - 1",
                        "number_value": 1,
                        "sequential_number": 2,
                        "text": "<p>l&ouml;mk</p>",
                        "amendment_paragraph_$": [],
                        "modified_final_version": "",
                        "reason": "",
                        "category_weight": 10000,
                        "state_extension": "<p>regeer</p>",
                        "recommendation_extension": None,
                        "sort_weight": 10000,
                        "created": 1584512346,
                        "last_modified": 1584512346,
                        "lead_motion_id": None,
                        "amendment_ids": [],
                        "sort_parent_id": None,
                        "sort_child_ids": [],
                        "origin_id": None,
                        "derived_motion_ids": [],
                        "forwarding_tree_motion_ids": [],
                        "recommendation_id": None,
                        "recommendation_extension_reference_ids": [],
                        "referenced_in_motion_recommendation_extension_ids": [],
                        "category_id": None,
                        "block_id": None,
                        "submitter_ids": [],
                        "supporter_ids": [],
                        "poll_ids": [],
                        "option_ids": [],
                        "change_recommendation_ids": [],
                        "statute_paragraph_id": None,
                        "comment_ids": [],
                        "agenda_item_id": None,
                        "tag_ids": [1],
                        "attachment_ids": [],
                        "projection_ids": [],
                        "personal_note_ids": [1],
                    }
                ],
                "list_of_speakers": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "speaker_ids": [],
                        "projection_ids": [],
                    }
                ],
                "tag": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "tagged_ids": ["motion/1"],
                        "name": "testag",
                    }
                ],
            }
        )
        request_data["meeting"]["meeting"][0]["personal_note_ids"] = [1]
        request_data["meeting"]["user"][0]["personal_note_$_ids"] = ["1"]
        request_data["meeting"]["user"][0]["personal_note_$1_ids"] = [1]
        request_data["meeting"]["meeting"][0]["motion_ids"] = [1]
        request_data["meeting"]["motion_state"][0]["motion_ids"] = [1]
        request_data["meeting"]["meeting"][0]["list_of_speakers_ids"] = [1]
        request_data["meeting"]["meeting"][0]["tag_ids"] = [1]

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "test"})
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3", {"username": "test 1", "group_$3_ids": [2], "group_$_ids": ["3"]}
        )
        self.assert_model_exists(
            "meeting/3",
            {
                "name": "Test",
                "description": "blablabla",
                "committee_id": 1,
                "enable_anonymous": False,
            },
        )
        meeting_2 = self.get_model("meeting/3")
        assert start <= meeting_2.get("imported_at", 0) <= start + 300
        self.assert_model_exists("projector/2", {"meeting_id": 3})
        self.assert_model_exists("group/2", {"user_ids": [1, 3]})
        self.assert_model_exists("personal_note/2", {"content_object_id": "motion/3"})
        self.assert_model_exists(
            "tag/2", {"tagged_ids": ["motion/3"], "name": "testag"}
        )
        self.assert_model_exists("committee/1", {"meeting_ids": [2, 3]})

    def test_no_permission(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
                "user/1": {
                    "username": "admin",
                    "organization_management_level": "can_manage_users",
                },
            }
        )
        response = self.request("meeting.import", self.create_request_data({}))
        self.assert_status_code(response, 403)
        assert (
            "Missing CommitteeManagementLevel: can_manage" in response.json["message"]
        )

    def test_clean_blobs(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        request_data = self.create_request_data(
            {
                "mediafile": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "blob": "blablabla",
                        "title": "A.txt",
                        "is_directory": False,
                        "filesize": 3,
                        "filename": "A.txt",
                        "mimetype": "text/plain",
                        "pdf_information": {},
                        "create_timestamp": 1584513771,
                        "is_public": True,
                        "access_group_ids": [],
                        "inherited_access_group_ids": [],
                        "parent_id": None,
                        "child_ids": [],
                        "list_of_speakers_id": None,
                        "projection_ids": [],
                        "attachment_ids": [],
                        "used_as_logo_$_in_meeting_id": [],
                        "used_as_font_$_in_meeting_id": [],
                    }
                ],
            }
        )
        request_data["meeting"]["meeting"][0]["mediafile_ids"] = [1]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        mediafile = self.get_model("mediafile/1")
        assert mediafile.get("blob") is None

    def test_meeting_user_ids(self) -> None:
        # Calculated field.
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        response = self.request("meeting.import", self.create_request_data({}))
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"user_ids": [1, 2]})

    def test_user_meeting_ids(self) -> None:
        # Calculated field.
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        response = self.request("meeting.import", self.create_request_data({}))
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"meeting_ids": [2]})

    def test_motion_recommendation_extension(self) -> None:
        # Special field
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        request_data = self.create_request_data(
            {
                "motion": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "list_of_speakers_id": 1,
                        "state_id": 1,
                        "title": "bla",
                        "state_id": 1,
                        "title": "bla",
                        "number": "1 - 1",
                        "number_value": 1,
                        "sequential_number": 2,
                        "text": "<p>l&ouml;mk</p>",
                        "amendment_paragraph_$": [],
                        "modified_final_version": "",
                        "reason": "",
                        "category_weight": 10000,
                        "state_extension": "<p>regeer</p>",
                        "recommendation_extension": None,
                        "sort_weight": 10000,
                        "created": 1584512346,
                        "last_modified": 1584512346,
                        "lead_motion_id": None,
                        "amendment_ids": [],
                        "sort_parent_id": None,
                        "sort_child_ids": [],
                        "origin_id": None,
                        "derived_motion_ids": [],
                        "forwarding_tree_motion_ids": [],
                        "recommendation_id": None,
                        "recommendation_extension_reference_ids": [],
                        "referenced_in_motion_recommendation_extension_ids": [],
                        "category_id": None,
                        "block_id": None,
                        "submitter_ids": [],
                        "supporter_ids": [],
                        "poll_ids": [],
                        "option_ids": [],
                        "change_recommendation_ids": [],
                        "statute_paragraph_id": None,
                        "comment_ids": [],
                        "agenda_item_id": None,
                        "tag_ids": [],
                        "attachment_ids": [],
                        "projection_ids": [],
                        "personal_note_ids": [],
                    },
                    {
                        "id": 2,
                        "meeting_id": 1,
                        "list_of_speakers_id": 2,
                        "state_id": 1,
                        "title": "bla",
                        "recommendation_extension": "bla[motion/1]bla",
                        "state_id": 1,
                        "title": "bla",
                        "number": "1 - 1",
                        "number_value": 1,
                        "sequential_number": 2,
                        "text": "<p>l&ouml;mk</p>",
                        "amendment_paragraph_$": [],
                        "modified_final_version": "",
                        "reason": "",
                        "category_weight": 10000,
                        "state_extension": "<p>regeer</p>",
                        "sort_weight": 10000,
                        "created": 1584512346,
                        "last_modified": 1584512346,
                        "lead_motion_id": None,
                        "amendment_ids": [],
                        "sort_parent_id": None,
                        "sort_child_ids": [],
                        "origin_id": None,
                        "derived_motion_ids": [],
                        "forwarding_tree_motion_ids": [],
                        "recommendation_id": None,
                        "recommendation_extension_reference_ids": [],
                        "referenced_in_motion_recommendation_extension_ids": [],
                        "category_id": None,
                        "block_id": None,
                        "submitter_ids": [],
                        "supporter_ids": [],
                        "poll_ids": [],
                        "option_ids": [],
                        "change_recommendation_ids": [],
                        "statute_paragraph_id": None,
                        "comment_ids": [],
                        "agenda_item_id": None,
                        "tag_ids": [],
                        "attachment_ids": [],
                        "projection_ids": [],
                        "personal_note_ids": [],
                    },
                ],
                "list_of_speakers": [
                    {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                    {
                        "id": 2,
                        "meeting_id": 1,
                        "content_object_id": "motion/2",
                        "closed": False,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                ],
            }
        )
        request_data["meeting"]["meeting"][0]["motion_ids"] = [1, 2]
        request_data["meeting"]["meeting"][0]["list_of_speakers_ids"] = [1, 2]
        request_data["meeting"]["motion_state"][0]["motion_ids"] = [1, 2]

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/3", {"recommendation_extension": "bla[motion/2]bla"}
        )

    def test_logo_dollar_id(self) -> None:
        # Template Relation Field
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        request_data = self.create_request_data(
            {
                "mediafile": [
                    {
                        "id": 3,
                        "meeting_id": 1,
                        "used_as_logo_$_in_meeting_id": ["web_header"],
                        "used_as_logo_$web_header_in_meeting_id": 1,
                        "title": "A.txt",
                        "is_directory": False,
                        "filesize": 3,
                        "filename": "A.txt",
                        "mimetype": "text/plain",
                        "pdf_information": {},
                        "create_timestamp": 1584513771,
                        "is_public": True,
                        "access_group_ids": [],
                        "inherited_access_group_ids": [],
                        "parent_id": None,
                        "child_ids": [],
                        "list_of_speakers_id": None,
                        "projection_ids": [],
                        "attachment_ids": [],
                        "used_as_font_$_in_meeting_id": [],
                        "blob": "bla",
                    }
                ]
            }
        )
        request_data["meeting"]["meeting"][0]["logo_$_id"] = ["web_header"]
        request_data["meeting"]["meeting"][0]["logo_$web_header_id"] = 3
        request_data["meeting"]["meeting"][0]["mediafile_ids"] = [3]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/1")
        self.assert_model_exists(
            "meeting/2", {"logo_$_id": ["web_header"], "logo_$web_header_id": 1}
        )

    def test_request_user_in_admin_group(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        response = self.request("meeting.import", self.create_request_data({}))
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"user_ids": [1, 2]})
        self.assert_model_exists("group/1", {"user_ids": [1, 2]})

    def test_field_check(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        request_data = self.create_request_data(
            {
                "mediafile": [
                    {
                        "id": 1,
                        "foobar": "test this",
                        "meeting_id": 1,
                        "list_of_speakers_id": 1,
                        "state_id": 1,
                        "title": "bla",
                        "forwarding_tree_motion_ids": [1],
                    },
                ],
                "list_of_speakers": [
                    {"id": 1, "meeting_id": 1, "content_object_id": "motion/1"},
                ],
            }
        )
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "Motion forwarding_tree_motion_ids should be empty."
            in response.json["message"]
        )

    def test_field_check(self) -> None:
        self.set_models(
            {
                "committee/1": {},
                "meeting/1": {},
                "motion/1": {},
            }
        )
        request_data = self.create_request_data(
            {
                "mediafile": [
                    {
                        "id": 1,
                        "foobar": "test this",
                        "meeting_id": 1,
                        "title": "A.txt",
                        "is_directory": False,
                        "filesize": 3,
                        "filename": "A.txt",
                        "mimetype": "text/plain",
                        "pdf_information": {},
                        "create_timestamp": 1584513771,
                        "is_public": True,
                        "access_group_ids": [],
                        "inherited_access_group_ids": [],
                        "parent_id": None,
                        "child_ids": [],
                        "list_of_speakers_id": None,
                        "projection_ids": [],
                        "attachment_ids": [],
                        "used_as_logo_$_in_meeting_id": [],
                        "used_as_font_$_in_meeting_id": [],
                        "blob": "bla",
                    }
                ]
            }
        )
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert "mediafile/1: Invalid fields foobar" in response.json["message"]
