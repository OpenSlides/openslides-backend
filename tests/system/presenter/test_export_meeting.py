from time import time

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.models.models import Meeting
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from .base import BasePresenterTestCase


class TestExportMeeting(BasePresenterTestCase):
    def test_correct(self) -> None:
        self.set_models({"meeting/1": {"name": "test_foo"}})
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        assert data["meeting"]["1"]["name"] == "test_foo"
        for collection in (
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
            "chat_message",
        ):
            assert data[collection] == {}

        assert data["_migration_index"]

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test_foo"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 403

    def test_with_locked_meeting(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "test_foo", "locked_from_inside": True},
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 400
        assert data["message"] == "Cannot export: meeting 1 is locked."

    def test_organization_tags_exclusion(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "name_foo", "organization_tag_ids": [12]},
                "organization_tag/12": {
                    "name": "name_bar",
                    "tagged_ids": ["meeting/1"],
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert "organization_tag" not in data
        assert data["meeting"]["1"].get("organization_tag_ids") is None

    def test_action_worker_import_preview_exclusion(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "name_foo"},
                "action_worker/1": {
                    "id": 1,
                    "name": "testcase",
                    "state": ActionWorkerState.END,
                    "created": round(time() - 3),
                    "timestamp": round(time()),
                },
                "import_preview/1": {
                    "id": 1,
                    "name": "topic",
                    "state": "done",
                    "created": round(time()),
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert "action_worker" not in data
        assert "import_preview" not in data

    def test_add_users(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "exported_meeting",
                    "user_ids": [1],
                    "group_ids": [11],
                    "present_user_ids": [1],
                    "meeting_user_ids": [1],
                },
                "gender/1": {"name": "male"},
                "user/1": {
                    "is_present_in_meeting_ids": [1],
                    "meeting_user_ids": [1],
                    "gender_id": 1,
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "group/11": {
                    "name": "group_in_meeting_1",
                    "meeting_id": 1,
                    "meeting_user_ids": [1],
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["user"]["1"]["organization_management_level"] == "superadmin"
        assert data["user"]["1"]["username"] == "admin"
        assert data["user"]["1"]["is_active"] is True
        assert data["user"]["1"]["meeting_ids"] == [1]
        assert data["user"]["1"]["is_present_in_meeting_ids"] == [1]
        assert data["user"]["1"]["gender"] == "male"
        assert data["meeting_user"]["1"]["group_ids"] == [11]

    def test_add_users_in_2_meetings(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "exported_meeting",
                    "user_ids": [1],
                    "group_ids": [11],
                    "present_user_ids": [1],
                    "meeting_user_ids": [1, 2],
                },
                "meeting/2": {
                    "name": "not exported_meeting",
                    "user_ids": [1],
                    "group_ids": [12],
                    "present_user_ids": [1],
                },
                "user/1": {
                    "is_present_in_meeting_ids": [1, 2],
                    "meeting_ids": [1, 2],
                    "meeting_user_ids": [1, 2],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "meeting_user/2": {
                    "meeting_id": 2,
                    "user_id": 1,
                    "group_ids": [12],
                },
                "group/11": {
                    "name": "group_in_meeting_1",
                    "meeting_id": 1,
                    "meeting_user_ids": [1],
                },
                "group/12": {
                    "name": "group_in_meeting_2",
                    "meeting_id": 2,
                    "meeting_user_ids": [2],
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["user"]["1"]["organization_management_level"] == "superadmin"
        assert data["user"]["1"]["username"] == "admin"
        assert data["user"]["1"]["is_active"] is True
        assert data["user"]["1"]["meeting_ids"] == [1]
        assert data["user"]["1"]["is_present_in_meeting_ids"] == [1]
        assert data["meeting_user"]["1"]["group_ids"] == [11]

    def test_export_meeting_with_ex_user(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "exported_meeting",
                    "motion_submitter_ids": [1],
                    "motion_ids": [1],
                    "list_of_speakers_ids": [1],
                    "personal_note_ids": [34],
                    "meeting_user_ids": [11, 12],
                },
                "user/11": {
                    "username": "exuser11",
                    "meeting_user_ids": [11],
                },
                "user/12": {
                    "username": "exuser12",
                    "meeting_user_ids": [12],
                },
                "meeting_user/11": {
                    "meeting_id": 1,
                    "user_id": 11,
                    "motion_submitter_ids": [1],
                },
                "meeting_user/12": {
                    "meeting_id": 1,
                    "user_id": 12,
                    "personal_note_ids": [34],
                },
                "motion/1": {
                    "list_of_speakers_id": 1,
                    "meeting_id": 1,
                    "sequential_number": 1,
                    "state_id": 1,
                    "submitter_ids": [1],
                    "title": "dummy",
                },
                "motion_submitter/1": {
                    "meeting_user_id": 11,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "list_of_speakers/1": {
                    "content_object_id": "motion/1",
                    "meeting_id": 1,
                    "sequential_number": 1,
                },
                "motion_state/1": {
                    "motion_ids": [1],
                },
                "personal_note/34": {
                    "meeting_user_id": 12,
                    "meeting_id": 1,
                    "note": "note_in_meeting1",
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["meeting"]["1"].get("user_ids") is None
        user11 = data["user"]["11"]
        assert user11.get("username") == "exuser11"
        assert user11.get("meeting_user_ids") == [11]
        self.assert_model_exists("meeting_user/11", {"motion_submitter_ids": [1]})
        user12 = data["user"]["12"]
        assert user12.get("username") == "exuser12"
        meeting_user_12 = data["meeting_user"]["12"]
        assert meeting_user_12.get("meeting_id") == 1
        assert meeting_user_12.get("user_id") == 12
        assert meeting_user_12.get("personal_note_ids") == [34]

    def test_export_meeting_find_special_users(self) -> None:
        """Find users in:
        Collection | Field
        meeting    | present_user_ids
        motion     | supporter_meeting_user_ids
        poll       | voted_ids
        vote       | delegated_meeting_user_id
        """

        self.set_models(
            {
                "meeting/1": {
                    "name": "exported_meeting",
                    "present_user_ids": [11],
                    "motion_ids": [30],
                    "poll_ids": [80],
                    "vote_ids": [120],
                    "meeting_user_ids": [112, 114],
                    "motion_submitter_ids": [1],
                },
                "user/11": {
                    "username": "exuser11",
                    "is_present_in_meeting_ids": [1],
                },
                "user/12": {
                    "username": "exuser12",
                    "meeting_user_ids": [112],
                },
                "user/13": {
                    "username": "exuser13",
                    "poll_voted_ids": [80],
                },
                "user/14": {
                    "username": "exuser14",
                    "meeting_user_ids": [114],
                    "delegated_vote_ids": [120],
                },
                "motion/30": {
                    "meeting_id": 1,
                    "supporter_ids": [1],
                },
                "poll/80": {
                    "meeting_id": 1,
                    "voted_ids": [13],
                },
                "vote/120": {
                    "meeting_id": 1,
                    "delegated_user_id": 14,
                    "user_id": 14,
                },
                "meeting_user/112": {
                    "meeting_id": 1,
                    "user_id": 12,
                    "motion_supporter_ids": [1],
                },
                "motion_supporter/1": {
                    "motion_id": 30,
                    "meeting_id": 1,
                    "meeting_user_id": 112,
                },
                "meeting_user/114": {
                    "meeting_id": 1,
                    "user_id": 14,
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["meeting"]["1"].get("user_ids") is None
        for id_ in ("11", "12", "13", "14"):
            assert data["user"][id_]

    def test_with_structured_published_orga_files(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "active_meeting_ids": [1],
                    "organization_tag_ids": [1],
                    "mediafile_ids": [1, 2, 3, 4, 5],
                    "published_mediafile_ids": [1, 2, 3, 4, 5],
                },
                "organization_tag/1": {
                    "name": "TEST",
                    "color": "#eeeeee",
                    "organization_id": 1,
                },
                "meeting/1": {
                    "committee_id": 1,
                    "language": "en",
                    "name": "Test",
                    "description": "blablabla",
                    "default_group_id": 1,
                    "admin_group_id": 2,
                    "motions_default_amendment_workflow_id": 1,
                    "motions_default_workflow_id": 1,
                    "reference_projector_id": 1,
                    "projector_countdown_default_time": 60,
                    "projector_countdown_warning_time": 5,
                    "projector_ids": [1],
                    "motion_state_ids": [1],
                    "motion_workflow_ids": [1],
                    "is_active_in_organization_id": 1,
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
                    "list_of_speakers_hide_contribution_count": True,
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_enable_pro_contra_speech": False,
                    "list_of_speakers_can_set_contribution_self": False,
                    "list_of_speakers_speaker_note_for_everyone": True,
                    "list_of_speakers_initially_closed": False,
                    "list_of_speakers_amount_last_on_projector": 0,
                    "motions_default_line_numbering": "outside",
                    "motions_line_length": 85,
                    "motions_reason_required": False,
                    "motions_origin_motion_toggle_default": False,
                    "motions_enable_origin_motion_display": False,
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
                    "motion_poll_default_method": "YNA",
                    "motion_poll_default_onehundred_percent_base": "YNA",
                    "motion_poll_default_backend": "fast",
                    "motion_poll_projection_name_order_first": "last_name",
                    "motion_poll_projection_max_columns": 6,
                    "users_enable_presence_view": False,
                    "users_enable_vote_weight": False,
                    "users_enable_vote_delegations": True,
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
                    "assignment_poll_default_onehundred_percent_base": "valid",
                    "assignment_poll_default_backend": "fast",
                    "poll_default_type": "analog",
                    "poll_default_onehundred_percent_base": "YNA",
                    "poll_default_backend": "fast",
                    "poll_default_live_voting_enabled": False,
                    "poll_couple_countdown": True,
                    **{field: [1] for field in Meeting.all_default_projectors()},
                    "meeting_mediafile_ids": [10, 20, 30, 40, 50],
                    "group_ids": [1, 2, 3],
                },
                "group/1": {
                    "meeting_id": 1,
                    "name": "default group",
                    "weight": 1,
                    "default_group_for_meeting_id": 1,
                    "meeting_mediafile_access_group_ids": [10, 40],
                    "meeting_mediafile_inherited_access_group_ids": [10, 20, 30, 40],
                },
                "group/2": {
                    "meeting_id": 1,
                    "name": "admin group",
                    "weight": 1,
                    "admin_group_for_meeting_id": 1,
                    "meeting_mediafile_access_group_ids": [10],
                    "meeting_mediafile_inherited_access_group_ids": [10, 20, 30],
                },
                "group/3": {
                    "meeting_id": 1,
                    "weight": 1,
                    "name": "third group",
                    "meeting_mediafile_access_group_ids": [50],
                },
                "motion_workflow/1": {
                    "meeting_id": 1,
                    "name": "blup",
                    "first_state_id": 1,
                    "default_amendment_workflow_meeting_id": 1,
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
                    **{field: 1 for field in Meeting.reverse_default_projectors()},
                },
                "mediafile/1": {
                    "title": "Mother of all directories (MOAD)",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "child_ids": [2, 3, 4, 5],
                    "is_directory": True,
                    "meeting_mediafile_ids": [10],
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/10": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "access_group_ids": [1, 2],
                    "inherited_access_group_ids": [1, 2],
                },
                "mediafile/2": {
                    "title": "Child_of_mother_of_all_directories.xlsx",
                    "filename": "COMOAD.xlsx",
                    "filesize": 10000,
                    "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "meeting_mediafile_ids": [20],
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/20": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 2,
                    "inherited_access_group_ids": [1, 2],
                },
                "mediafile/3": {
                    "title": "Child_of_mother_of_all_directories.pdf",
                    "filename": "COMOAD.pdf",
                    "filesize": 750000,
                    "mimetype": "application/pdf",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "pdf_information": {"pages": 1},
                    "meeting_mediafile_ids": [30],
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/30": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 3,
                    "inherited_access_group_ids": [1, 2],
                },
                "mediafile/4": {
                    "title": "Child_of_mother_of_all_directories_with_limited_access.txt",
                    "filename": "COMOADWLA.txt",
                    "filesize": 100,
                    "mimetype": "text/plain",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "meeting_mediafile_ids": [40],
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/40": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 4,
                    "access_group_ids": [1],
                    "inherited_access_group_ids": [1],
                },
                "mediafile/5": {
                    "title": "Hidden_child_of_mother_of_all_directories.csv",
                    "filename": "HCOMOAD.csv",
                    "filesize": 420,
                    "mimetype": "text/csv",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "meeting_mediafile_ids": [50],
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/50": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 5,
                    "access_group_ids": [3],
                    "inherited_access_group_ids": [],
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        # Should not include mediafile ids bc presenter does not include orga mediafiles
        assert data["mediafile"] == {}
