from typing import Any, Dict

from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestCheckDatabase(BasePresenterTestCase):
    def test_found_errors(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test_foo"},
                "meeting/2": {"name": "test_bar"},
            }
        )
        status_code, data = self.request("check_database", {})
        assert status_code == 200
        assert data["ok"] is False
        assert "Meeting 1" in data["errors"]
        assert "meeting/1: Missing fields" in data["errors"]
        assert "Meeting 2" in data["errors"]
        assert "meeting/2: Missing fields" in data["errors"]

    def get_meeting_defaults(self) -> Dict[str, Any]:
        return {
            "motions_export_title": "Motions",
            "motions_preamble": "blablabla",
            "welcome_title": "Welcome to OpenSlides",
            "welcome_text": "Space for your welcome text.",
            "enable_anonymous": False,
            "conference_show": False,
            "conference_auto_connect": False,
            "conference_los_restriction": False,
            "conference_open_microphone": False,
            "conference_open_video": False,
            "conference_auto_connect_next_speakers": 0,
            "conference_enable_helpdesk": False,
            "applause_enable": False,
            "applause_type": "applause-type-bar",
            "applause_show_level": False,
            "applause_min_amount": 1,
            "applause_max_amount": 0,
            "applause_timeout": 5,
            "export_csv_encoding": "utf-8",
            "export_csv_separator": ";",
            "export_pdf_pagenumber_alignment": "center",
            "export_pdf_fontsize": 10,
            "export_pdf_line_height": 1.25,
            "export_pdf_page_margin_left": 20,
            "export_pdf_page_margin_top": 25,
            "export_pdf_page_margin_right": 20,
            "export_pdf_page_margin_bottom": 20,
            "export_pdf_pagesize": "A4",
            "agenda_show_subtitles": False,
            "agenda_enable_numbering": False,
            "agenda_numeral_system": "arabic",
            "agenda_item_creation": "default_no",
            "agenda_new_items_default_visibility": "internal",
            "agenda_show_internal_items_on_projector": False,
            "list_of_speakers_amount_next_on_projector": -1,
            "list_of_speakers_couple_countdown": True,
            "list_of_speakers_show_amount_of_speakers_on_slide": True,
            "list_of_speakers_present_users_only": True,
            "list_of_speakers_show_first_contribution": True,
            "list_of_speakers_enable_point_of_order_speakers": True,
            "list_of_speakers_enable_pro_contra_speech": False,
            "list_of_speakers_can_set_contribution_self": False,
            "list_of_speakers_speaker_note_for_everyone": True,
            "list_of_speakers_initially_closed": False,
            "list_of_speakers_amount_last_on_projector": 0,
            "motions_default_line_numbering": "outside",
            "motions_line_length": 85,
            "motions_reason_required": False,
            "motions_enable_text_on_projector": False,
            "motions_enable_reason_on_projector": False,
            "motions_enable_sidebox_on_projector": False,
            "motions_enable_recommendation_on_projector": True,
            "motions_show_referring_motions": True,
            "motions_show_sequential_number": True,
            "motions_recommendation_text_mode": "diff",
            "motions_default_sorting": "number",
            "motions_number_type": "per_category",
            "motions_number_min_digits": 2,
            "motions_number_with_blank": False,
            "motions_statutes_enabled": False,
            "motions_amendments_enabled": True,
            "motions_amendments_in_main_list": True,
            "motions_amendments_of_amendments": False,
            "motions_amendments_prefix": "A",
            "motions_amendments_text_mode": "paragraph",
            "motions_amendments_multiple_paragraphs": True,
            "motions_supporters_min_amount": 0,
            "motions_export_submitter_recommendation": True,
            "motions_export_follow_recommendation": False,
            "motion_poll_ballot_paper_selection": "CUSTOM_NUMBER",
            "motion_poll_ballot_paper_number": 8,
            "motion_poll_default_type": "pseudoanonymous",
            "motion_poll_default_100_percent_base": "YNA",
            "motion_poll_default_backend": "fast",
            "users_sort_by": "first_name",
            "users_enable_presence_view": False,
            "users_enable_vote_weight": False,
            "users_allow_self_set_present": True,
            "users_pdf_welcometitle": "Welcome to OpenSlides",
            "users_pdf_welcometext": "blablabla",
            "users_email_sender": "OpenSlides",
            "users_email_subject": "OpenSlides access data",
            "users_email_body": "blablabla",
            "assignments_export_title": "Elections",
            "assignment_poll_ballot_paper_selection": "CUSTOM_NUMBER",
            "assignment_poll_ballot_paper_number": 8,
            "assignment_poll_add_candidates_to_list_of_speakers": False,
            "assignment_poll_enable_max_votes_per_option": False,
            "assignment_poll_sort_poll_result_by_votes": True,
            "assignment_poll_default_type": "pseudoanonymous",
            "assignment_poll_default_method": "Y",
            "assignment_poll_default_100_percent_base": "valid",
            "assignment_poll_default_backend": "fast",
            "poll_default_type": "analog",
            "poll_default_100_percent_base": "YNA",
            "poll_default_backend": "fast",
            "poll_couple_countdown": True,
        }

    def test_correct(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "active_meeting_ids": [1],
                    "organization_tag_ids": [1],
                },
                "organization_tag/1": {
                    "name": "TEST",
                    "color": "#eeeeee",
                    "organization_id": 1,
                },
                "committee/1": {"organization_id": 1},
                "meeting/1": {
                    "committee_id": 1,
                    "name": "Test",
                    "description": "blablabla",
                    "default_group_id": 1,
                    "admin_group_id": 2,
                    "motions_default_amendment_workflow_id": 1,
                    "motions_default_statute_amendment_workflow_id": 1,
                    "motions_default_workflow_id": 1,
                    "reference_projector_id": 1,
                    "projector_countdown_default_time": 60,
                    "projector_countdown_warning_time": 5,
                    "projector_ids": [1],
                    "group_ids": [1, 2],
                    "motion_state_ids": [1],
                    "motion_workflow_ids": [1],
                    "logo_$_id": None,
                    "font_$_id": [],
                    "default_projector_$_id": [],
                    "is_active_in_organization_id": 1,
                    **self.get_meeting_defaults(),
                },
                "group/1": {
                    "meeting_id": 1,
                    "name": "default group",
                    "weight": 1,
                    "default_group_for_meeting_id": 1,
                },
                "group/2": {
                    "meeting_id": 1,
                    "name": "admin group",
                    "weight": 1,
                    "admin_group_for_meeting_id": 1,
                },
                "motion_workflow/1": {
                    "meeting_id": 1,
                    "name": "blup",
                    "first_state_id": 1,
                    "default_amendment_workflow_meeting_id": 1,
                    "default_statute_amendment_workflow_meeting_id": 1,
                    "default_workflow_meeting_id": 1,
                    "state_ids": [1],
                    "sequential_number": 1,
                },
                "motion_state/1": {
                    "css_class": "lightblue",
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "name": "test",
                    "weight": 1,
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                    "restrictions": [],
                    "allow_support": False,
                    "allow_create_poll": False,
                    "allow_submitter_edit": False,
                    "set_number": True,
                    "show_state_extension_field": False,
                    "merge_amendment_into_final": "undefined",
                    "show_recommendation_extension_field": False,
                },
                "projector/1": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    "name": "Default projector",
                    "used_as_default_$_in_meeting_id": [],
                    "scale": 0,
                    "scroll": 0,
                    "width": 1200,
                    "aspect_ratio_numerator": 16,
                    "aspect_ratio_denominator": 9,
                    "color": "#000000",
                    "background_color": "#ffffff",
                    "header_background_color": "#317796",
                    "header_font_color": "#ffffff",
                    "header_h1_color": "#ffffff",
                    "chyron_background_color": "#ffffff",
                    "chyron_font_color": "#ffffff",
                    "show_header_footer": True,
                    "show_title": True,
                    "show_logo": True,
                    "show_clock": True,
                },
            }
        )
        status_code, data = self.request("check_database", {})
        assert status_code == 200
        assert data["ok"] is True
        assert not data["errors"]

    def get_new_user(self, username: str, datapart: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "username": username,
            "group_$_ids": ["1"],
            "group_$1_ids": [1],
            "can_change_own_password": False,
            "is_physical_person": True,
            "default_vote_weight": "1.000000",
            **datapart,
        }

    def test_correct_relations(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "active_meeting_ids": [],
                    "archived_meeting_ids": [1],
                    "organization_tag_ids": [1],
                    "template_meeting_ids": [1],
                },
                "organization_tag/1": {
                    "name": "TEST",
                    "color": "#eeeeee",
                    "organization_id": 1,
                    "tagged_ids": ["meeting/1"],
                },
                "committee/1": {"organization_id": 1, "default_meeting_id": 1},
                "meeting/1": {
                    "committee_id": 1,
                    "name": "Test",
                    "description": "blablabla",
                    "default_group_id": 1,
                    "admin_group_id": 2,
                    "motions_default_amendment_workflow_id": 1,
                    "motions_default_statute_amendment_workflow_id": 1,
                    "motions_default_workflow_id": 1,
                    "reference_projector_id": 1,
                    "projector_countdown_default_time": 60,
                    "projector_countdown_warning_time": 5,
                    "projector_ids": [1],
                    "group_ids": [1, 2],
                    "motion_state_ids": [1],
                    "motion_workflow_ids": [1],
                    "default_projector_$_id": [],
                    "motion_ids": [1],
                    "motion_submitter_ids": [5],
                    "list_of_speakers_ids": [6, 11],
                    "vote_ids": [7],
                    "option_ids": [8],
                    "assignment_candidate_ids": [9],
                    "assignment_ids": [10],
                    # relation fields.
                    "is_archived_in_organization_id": 1,
                    "template_for_organization_id": 1,
                    "default_meeting_for_committee_id": 1,
                    "organization_tag_ids": [1],
                    "user_ids": [1, 2, 3, 4, 5, 6],
                    "present_user_ids": [2],
                    "mediafile_ids": [1, 2],
                    "logo_$_id": ["web_header"],
                    "logo_$web_header_id": 1,
                    "font_$_id": ["bold"],
                    "font_$bold_id": 2,
                    **self.get_meeting_defaults(),
                },
                "group/1": {
                    "meeting_id": 1,
                    "name": "default group",
                    "weight": 1,
                    "default_group_for_meeting_id": 1,
                    "user_ids": [1, 2, 3, 4, 5, 6],
                },
                "group/2": {
                    "meeting_id": 1,
                    "name": "admin group",
                    "weight": 1,
                    "admin_group_for_meeting_id": 1,
                },
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "can_change_own_password": False,
                    "is_physical_person": True,
                    "default_vote_weight": "1.000000",
                },
                "user/2": self.get_new_user(
                    "present_user",
                    {
                        "is_present_in_meeting_ids": [1],
                    },
                ),
                "user/3": self.get_new_user(
                    "submitter_user",
                    {
                        "submitted_motion_$_ids": ["1"],
                        "submitted_motion_$1_ids": [5],
                    },
                ),
                "user/4": self.get_new_user(
                    "vote_user",
                    {
                        "vote_$_ids": ["1"],
                        "vote_$1_ids": [7],
                    },
                ),
                "user/5": self.get_new_user(
                    "delegated_user",
                    {
                        "vote_delegated_vote_$_ids": ["1"],
                        "vote_delegated_vote_$1_ids": [7],
                    },
                ),
                "user/6": self.get_new_user(
                    "candidate_user",
                    {
                        "assignment_candidate_$_ids": ["1"],
                        "assignment_candidate_$1_ids": [9],
                    },
                ),
                "motion_workflow/1": {
                    "meeting_id": 1,
                    "name": "blup",
                    "first_state_id": 1,
                    "default_amendment_workflow_meeting_id": 1,
                    "default_statute_amendment_workflow_meeting_id": 1,
                    "default_workflow_meeting_id": 1,
                    "state_ids": [1],
                    "sequential_number": 1,
                },
                "motion_state/1": {
                    "css_class": "lightblue",
                    "meeting_id": 1,
                    "workflow_id": 1,
                    "name": "test",
                    "weight": 1,
                    "workflow_id": 1,
                    "first_state_of_workflow_id": 1,
                    "restrictions": [],
                    "allow_support": False,
                    "allow_create_poll": False,
                    "allow_submitter_edit": False,
                    "set_number": True,
                    "show_state_extension_field": False,
                    "merge_amendment_into_final": "undefined",
                    "show_recommendation_extension_field": False,
                    "motion_ids": [1],
                },
                "projector/1": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "used_as_reference_projector_meeting_id": 1,
                    "name": "Default projector",
                    "used_as_default_$_in_meeting_id": [],
                    "scale": 0,
                    "scroll": 0,
                    "width": 1200,
                    "aspect_ratio_numerator": 16,
                    "aspect_ratio_denominator": 9,
                    "color": "#000000",
                    "background_color": "#ffffff",
                    "header_background_color": "#317796",
                    "header_font_color": "#ffffff",
                    "header_h1_color": "#ffffff",
                    "chyron_background_color": "#ffffff",
                    "chyron_font_color": "#ffffff",
                    "show_header_footer": True,
                    "show_title": True,
                    "show_logo": True,
                    "show_clock": True,
                },
                "mediafile/1": {
                    "is_public": True,
                    "owner_id": "meeting/1",
                    "used_as_logo_$_in_meeting_id": ["web_header"],
                    "used_as_logo_$web_header_in_meeting_id": 1,
                },
                "mediafile/2": {
                    "is_public": True,
                    "owner_id": "meeting/1",
                    "used_as_font_$_in_meeting_id": ["bold"],
                    "used_as_font_$bold_in_meeting_id": 1,
                },
                "motion/1": {
                    "submitter_ids": [5],
                    "meeting_id": 1,
                    "sequential_number": 1,
                    "title": "test Motion",
                    "category_weight": 10000,
                    "sort_weight": 10000,
                    "start_line_number": 1,
                    "state_id": 1,
                    "list_of_speakers_id": 6,
                },
                "motion_submitter/5": {
                    "user_id": 3,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "list_of_speakers/6": {
                    "closed": True,
                    "sequential_number": 1,
                    "content_object_id": "motion/1",
                    "meeting_id": 1,
                },
                "vote/7": {
                    "user_token": "test",
                    "option_id": 8,
                    "user_id": 4,
                    "delegated_user_id": 5,
                    "meeting_id": 1,
                },
                "option/8": {
                    "vote_ids": [7],
                    "meeting_id": 1,
                    "weight": 10000,
                },
                "assignment_candidate/9": {
                    "weight": 10000,
                    "assignment_id": 10,
                    "user_id": 6,
                    "meeting_id": 1,
                },
                "assignment/10": {
                    "title": "test",
                    "open_posts": 0,
                    "phase": "search",
                    "sequential_number": 1,
                    "candidate_ids": [9],
                    "meeting_id": 1,
                    "list_of_speakers_id": 11,
                },
                "list_of_speakers/11": {
                    "closed": True,
                    "sequential_number": 1,
                    "content_object_id": "assignment/10",
                    "meeting_id": 1,
                },
            }
        )
        status_code, data = self.request("check_database", {})
        assert status_code == 200
        if not data["ok"]:
            print(data)
        assert data["ok"] is True
        assert not data["errors"]

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test_foo"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )
        status_code, data = self.request("check_database", {})
        assert status_code == 403
        assert "Missing permission: superadmin" in data["message"]
