from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.models.models import Poll
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from .base import BasePresenterTestCase


class TestExportMeeting(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1, {"name": "exported_meeting"})

    def test_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "start_time": datetime.fromtimestamp(
                        626637600, tz=ZoneInfo("Europe/Berlin")
                    ),
                    "end_time": datetime.fromtimestamp(
                        654908400, tz=ZoneInfo("Europe/Berlin")
                    ),
                }
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        meeting = data["meeting"]["1"]
        assert meeting["name"] == "exported_meeting"
        # TODO: Backend is currently automatically transforming all timestamps to UTC
        # When that is changed, these checks will need to be changed to something like
        # "1989-11-09T19:00:00+01:00" and "1990-10-03T00:00:00+01:00" respectively
        assert meeting["start_time"] == "1989-11-09T18:00:00+00:00"
        assert meeting["end_time"] == "1990-10-02T23:00:00+00:00"
        for collection in (
            "group",
            "projector",
            "motion_workflow",
            "motion_state",
        ):
            assert len(data.get(collection, {}))
        for collection in (
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
            "poll",
            "vote",
            "assignment",
            "assignment_candidate",
            "mediafile",
            "projection",
            "projector_message",
            "projector_countdown",
            "chat_group",
            "chat_message",
        ):
            assert data[collection] == {}
        assert data["_migration_index"]

    def test_no_permissions(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 403

    def test_with_locked_meeting(self) -> None:
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 400
        assert data["message"] == "Cannot export: meeting 1 is locked."

    def test_organization_tags_exclusion(self) -> None:
        self.set_models(
            {
                "organization_tag/12": {
                    "name": "name_bar",
                    "tagged_ids": ["meeting/1"],
                    "color": "#123456",
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
                "action_worker/1": {
                    "id": 1,
                    "name": "testcase",
                    "state": ActionWorkerState.END,
                    "created": datetime.fromtimestamp(1234565),
                    "timestamp": datetime.fromtimestamp(1234567),
                    "user_id": 1,
                },
                "import_preview/1": {
                    "id": 1,
                    "name": "topic",
                    "state": "done",
                    "created": datetime.fromtimestamp(1234567),
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert "action_worker" not in data
        assert "import_preview" not in data

    def test_add_users(self) -> None:
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "meeting/1": {"present_user_ids": [1]},
                "gender/1": {"name": "male"},
                "user/1": {"gender_id": 1, "default_vote_weight": "2.000000"},
                "meeting_user/1": {"vote_weight": Decimal("3.000001")},
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200

        user = data["user"]["1"]
        assert user["organization_management_level"] == "superadmin"
        assert user["username"] == "admin"
        assert user["is_active"] is True
        assert user["is_present_in_meeting_ids"] == [1]
        assert user["gender"] == "male"
        assert user["default_vote_weight"] == "2.000000"

        assert data["meeting_user"]["1"]["group_ids"] == [1]
        assert data["meeting_user"]["1"]["vote_weight"] == "3.000001"

    def test_add_users_in_2_meetings(self) -> None:
        self.create_meeting(
            4, {"name": "not exported_meeting", "present_user_ids": [1]}
        )
        self.set_user_groups(1, [1, 4])
        self.set_models({"meeting/1": {"present_user_ids": [1]}})
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200

        user = data["user"]["1"]
        assert user["organization_management_level"] == "superadmin"
        assert user["username"] == "admin"
        assert user["is_active"] is True
        assert user["is_present_in_meeting_ids"] == [1]

        assert data["meeting_user"]["1"]["group_ids"] == [1]

    def test_export_meeting_with_ex_user(self) -> None:
        self.create_motion(1, 1)
        self.set_models(
            {"user/11": {"username": "exuser11"}, "user/12": {"username": "exuser12"}}
        )
        self.set_user_groups(11, [1])
        self.set_user_groups(12, [1])
        self.set_models(
            {
                "motion_submitter/1": {
                    "meeting_user_id": 1,
                    "motion_id": 1,
                    "meeting_id": 1,
                },
                "list_of_speakers/1": {
                    "content_object_id": "motion/1",
                    "meeting_id": 1,
                },
                "personal_note/34": {
                    "meeting_user_id": 2,
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
        assert user11.get("meeting_user_ids") == [1]

        meeting_user_1 = data["meeting_user"]["1"]
        assert meeting_user_1.get("meeting_id") == 1
        assert meeting_user_1.get("user_id") == 11
        assert meeting_user_1.get("motion_submitter_ids") == [1]

        user12 = data["user"]["12"]
        assert user12.get("username") == "exuser12"
        assert user12.get("meeting_user_ids") == [2]

        meeting_user_2 = data["meeting_user"]["2"]
        assert meeting_user_2.get("meeting_id") == 1
        assert meeting_user_2.get("user_id") == 12
        assert meeting_user_2.get("personal_note_ids") == [34]

    def test_export_meeting_find_special_users(self) -> None:
        """Find users in:
        Collection          | Field
        meeting             | present_user_ids

        Find meeting_users in:
        Collection          | Field
        poll                | voted_ids
        motion              | supporter_meeting_user_ids
        ballot              | acting_meeting_user_id
        ballot              | represented_meeting_user_id
        poll_config_option  | meeting_user_id
        """
        self.create_meeting()
        self.create_motion(1, 30)
        self.set_models(
            {
                "meeting/1": {"present_user_ids": [11]},
                "group/1": {"meeting_user_ids": [112, 114]},
                "user/11": {"username": "exuser11"},
                "user/12": {"username": "exuser12"},
                "user/13": {"username": "exuser13"},
                "user/14": {"username": "exuser14"},
                "meeting_user/112": {"meeting_id": 1, "user_id": 12},
                "motion_supporter/1": {
                    "motion_id": 30,
                    "meeting_id": 1,
                    "meeting_user_id": 112,
                },
                "meeting_user/113": {"meeting_id": 1, "user_id": 13},
                "meeting_user/114": {"meeting_id": 1, "user_id": 14},
                "poll/80": {
                    "title": "Poll 80",
                    "meeting_id": 1,
                    "content_object_id": "assignment/10",
                    "visibility": Poll.VISIBILITY_NAMED,
                    "config_id": "poll_config_approval/90",
                    "state": Poll.STATE_STARTED,
                    "voted_ids": [114],
                },
                "poll_config_approval/90": {"poll_id": 80},
                "poll_config_option/100": {
                    "poll_config_id": "poll_config_approval/90",
                    "meeting_user_id": 113,
                },
                "ballot/120": {
                    "poll_id": 80,
                    "value": "yes",
                    "represented_meeting_user_id": 114,
                    "acting_meeting_user_id": 114,
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["meeting"]["1"].get("user_ids") is None
        for id_ in range(11, 15):
            assert data["user"][str(id_)]
        for id_ in range(112, 115):
            assert data["meeting_user"][str(id_)]

        assert data["meeting"]["1"]["present_user_ids"] == [11]
        assert data["user"]["11"]["is_present_in_meeting_ids"] == [1]

        assert data["motion"]["30"]["supporter_meeting_user_ids"] == [112]
        assert data["meeting_user"]["112"]["supported_motion_ids"] == [30]

        assert data["poll_config_option"]["100"]["meeting_user_id"] == 113
        assert data["meeting_user"]["113"]["poll_option_ids"] == [100]

        assert data["poll"]["80"]["voted_ids"] == [114]
        assert data["meeting_user"]["114"]["poll_voted_ids"] == [80]
        assert data["ballot"]["120"]["c"] == 114
        assert data["ballot"]["120"]["represented_meeting_user_id"] == 114
        assert data["meeting_user"]["114"]["acting_ballot_ids"] == [120]
        assert data["meeting_user"]["114"]["represented_ballot_ids"] == [120]

    def test_with_structured_published_orga_files(self) -> None:
        self.set_models(
            {
                "organization_tag/1": {
                    "name": "TEST",
                    "color": "#eeeeee",
                    "organization_id": 1,
                },
                "meeting/1": {
                    "name": "Test",
                    "description": "blablabla",
                    "projector_countdown_default_time": 60,
                    "projector_countdown_warning_time": 5,
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
                    "poll_default_live_voting_enabled": False,
                    "poll_couple_countdown": True,
                },
                "group/1": {
                    "meeting_mediafile_access_group_ids": [10, 40],
                    "meeting_mediafile_inherited_access_group_ids": [10, 20, 30, 40],
                },
                "group/2": {
                    "meeting_mediafile_access_group_ids": [10],
                    "meeting_mediafile_inherited_access_group_ids": [10, 20, 30],
                },
                "group/3": {
                    "meeting_mediafile_access_group_ids": [50],
                },
                "mediafile/1": {
                    "title": "Mother of all directories (MOAD)",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "is_directory": True,
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/10": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 1,
                },
                "mediafile/2": {
                    "title": "Child_of_mother_of_all_directories.xlsx",
                    "filename": "COMOAD.xlsx",
                    "filesize": 10000,
                    "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/20": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 2,
                },
                "mediafile/3": {
                    "title": "Child_of_mother_of_all_directories.pdf",
                    "filename": "COMOAD.pdf",
                    "filesize": 750000,
                    "mimetype": "application/pdf",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "pdf_information": Jsonb({"pages": 1}),
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/30": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 3,
                },
                "mediafile/4": {
                    "title": "Child_of_mother_of_all_directories_with_limited_access.txt",
                    "filename": "COMOADWLA.txt",
                    "filesize": 100,
                    "mimetype": "text/plain",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/40": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 4,
                },
                "mediafile/5": {
                    "title": "Hidden_child_of_mother_of_all_directories.csv",
                    "filename": "HCOMOAD.csv",
                    "filesize": 420,
                    "mimetype": "text/csv",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "published_to_meetings_in_organization_id": 1,
                },
                "meeting_mediafile/50": {
                    "is_public": False,
                    "meeting_id": 1,
                    "mediafile_id": 5,
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        # Should not include mediafile ids bc presenter does not include orga mediafiles
        assert data["mediafile"] == {}
