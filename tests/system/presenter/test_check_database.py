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
                    # fields with default value
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
