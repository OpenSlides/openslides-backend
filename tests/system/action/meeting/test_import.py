import base64
import time
from typing import Any

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.migrations import get_backend_migration_index
from openslides_backend.models.models import Meeting
from openslides_backend.shared.util import (
    ONE_ORGANIZATION_FQID,
    ONE_ORGANIZATION_ID,
    get_initial_data_file,
)
from tests.system.action.base import BaseActionTestCase
from tests.system.util import CountDatastoreCalls, Profiler, performance

current_migration_index = get_backend_migration_index()


class MeetingImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "active_meeting_ids": [1],
                    "committee_ids": [1],
                },
                "committee/1": {"organization_id": 1, "meeting_ids": [1]},
                "meeting/1": {
                    "committee_id": 1,
                    "group_ids": [1],
                    "is_active_in_organization_id": ONE_ORGANIZATION_ID,
                },
                "group/1": {"meeting_id": 1, "name": "group1_m1"},
                "projector/1": {"meeting_id": 1},
                "motion/1": {
                    "meeting_id": 1,
                    "sequential_number": 26,
                    "number_value": 31,
                },
            }
        )

    def create_request_data(
        self, datapart: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "committee_id": 1,
            "meeting": {
                "_migration_index": current_migration_index,
                "meeting": {
                    "1": {
                        "id": 1,
                        "language": "en",
                        "name": "Test",
                        "description": "blablabla",
                        "admin_group_id": 1,
                        "default_group_id": 2,
                        "motions_default_amendment_workflow_id": 1,
                        "motions_default_statute_amendment_workflow_id": 1,
                        "motions_default_workflow_id": 1,
                        "projector_countdown_default_time": 60,
                        "projector_countdown_warning_time": 60,
                        "reference_projector_id": 1,
                        "user_ids": [1],
                        "imported_at": None,
                        "custom_translations": None,
                        "template_for_organization_id": None,
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
                        "conference_enable_helpdesk": False,
                        "applause_enable": True,
                        "applause_type": "applause-type-particles",
                        "applause_show_level": True,
                        "applause_min_amount": 2,
                        "applause_max_amount": 3,
                        "applause_timeout": 6,
                        "applause_particle_image_url": "test",
                        "export_csv_encoding": "utf-8",
                        "export_csv_separator": ",",
                        "export_pdf_pagenumber_alignment": "center",
                        "export_pdf_fontsize": 10,
                        "export_pdf_pagesize": "A4",
                        "export_pdf_line_height": 1.25,
                        "export_pdf_page_margin_left": 20,
                        "export_pdf_page_margin_top": 25,
                        "export_pdf_page_margin_right": 20,
                        "export_pdf_page_margin_bottom": 20,
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
                        "motion_poll_default_type": "pseudoanonymous",
                        "motion_poll_default_onehundred_percent_base": "YNA",
                        "motion_poll_default_group_ids": [],
                        "motion_poll_default_backend": "fast",
                        "users_enable_presence_view": True,
                        "users_enable_vote_weight": True,
                        "users_enable_vote_delegations": True,
                        "users_allow_self_set_present": True,
                        "users_pdf_welcometitle": "Welcome to OpenSlides",
                        "users_pdf_welcometext": "[Place for your welcome and help text.]",
                        "users_pdf_wlan_ssid": "",
                        "users_pdf_wlan_password": "",
                        "users_pdf_wlan_encryption": "",
                        "users_email_sender": "noreply@yourdomain.com",
                        "users_email_replyto": "",
                        "users_email_subject": "OpenSlides access data",
                        "users_email_body": "Dear {name},\n\nthis is your personal OpenSlides login:\n\n{url}\nUsername: {username}\nPassword: {password}\n\n\nThis email was generated automatically.",
                        "assignments_export_title": "Elections",
                        "assignments_export_preamble": "",
                        "assignment_poll_ballot_paper_selection": "CUSTOM_NUMBER",
                        "assignment_poll_ballot_paper_number": 8,
                        "assignment_poll_add_candidates_to_list_of_speakers": True,
                        "assignment_poll_enable_max_votes_per_option": None,
                        "assignment_poll_sort_poll_result_by_votes": True,
                        "assignment_poll_default_type": "pseudoanonymous",
                        "assignment_poll_default_method": "votes",
                        "assignment_poll_default_onehundred_percent_base": "valid",
                        "assignment_poll_default_group_ids": [],
                        "assignment_poll_default_backend": "fast",
                        "poll_ballot_paper_selection": "CUSTOM_NUMBER",
                        "poll_ballot_paper_number": 8,
                        "poll_sort_poll_result_by_votes": True,
                        "poll_default_type": "pseudoanonymous",
                        "poll_default_method": "votes",
                        "poll_default_onehundred_percent_base": "valid",
                        "poll_default_group_ids": [],
                        "poll_default_backend": "fast",
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
                        "group_ids": [1, 2],
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
                        "chat_message_ids": [],
                        "committee_id": None,
                        "is_active_in_organization_id": None,
                        "is_archived_in_organization_id": None,
                        "default_meeting_for_committee_id": None,
                        "organization_tag_ids": [],
                        "present_user_ids": [],
                        "list_of_speakers_countdown_id": None,
                        "poll_countdown_id": None,
                        **{field: [1] for field in Meeting.all_default_projectors()},
                        "projection_ids": [],
                        "meeting_user_ids": [11],
                    }
                },
                "user": {
                    "1": self.get_user_data(
                        1,
                        {
                            "meeting_user_ids": [11],
                            "is_active": True,
                        },
                    ),
                },
                "meeting_user": {
                    "11": {"id": 11, "meeting_id": 1, "user_id": 1, "group_ids": [1]}
                },
                "group": {
                    "1": self.get_group_data(
                        1,
                        {
                            "name": "imported admin group1",
                            "meeting_user_ids": [11],
                            "admin_group_for_meeting_id": 1,
                        },
                    ),
                    "2": self.get_group_data(
                        2,
                        {
                            "name": "imported default group2",
                            "meeting_user_ids": [],
                            "default_group_for_meeting_id": 1,
                        },
                    ),
                },
                "motion_workflow": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "name": "blup",
                        "first_state_id": 1,
                        "default_amendment_workflow_meeting_id": 1,
                        "default_statute_amendment_workflow_meeting_id": 1,
                        "default_workflow_meeting_id": 1,
                        "state_ids": [1],
                        "sequential_number": 1,
                    }
                },
                "motion_state": {
                    "1": {
                        "id": 1,
                        "css_class": "lightblue",
                        "meeting_id": 1,
                        "workflow_id": 1,
                        "name": "test",
                        "weight": 1,
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
                },
                "projector": {
                    "1": {
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
                        **{field: 1 for field in Meeting.reverse_default_projectors()},
                        "sequential_number": 1,
                    }
                },
            },
        }
        if datapart:
            for collection, models in datapart.items():
                if collection not in data["meeting"]:
                    data["meeting"][collection] = models
                else:
                    data["meeting"][collection].update(models)

        return data

    def get_user_data(self, obj_id: int, data: dict[str, Any] = {}) -> dict[str, Any]:
        return {
            "id": obj_id,
            "password": "",
            "username": "test",
            "committee_ids": [1],
            "committee_management_ids": [],
            "title": "",
            "pronoun": "",
            "first_name": "",
            "last_name": "Administrator",
            "is_active": True,
            "is_physical_person": True,
            "default_password": "admin",
            "can_change_own_password": True,
            "gender": "male",
            "email": "",
            "default_vote_weight": "1.000000",
            "last_email_sent": None,
            "is_demo_user": False,
            "organization_management_level": None,
            "is_present_in_meeting_ids": [],
            "meeting_ids": [1],
            "organization_id": 1,
            **data,
        }

    def get_group_data(self, obj_id: int, data: dict[str, Any] = {}) -> dict[str, Any]:
        return {
            "id": obj_id,
            "meeting_id": 1,
            "name": "testgroup",
            "weight": obj_id,
            "admin_group_for_meeting_id": None,
            "default_group_for_meeting_id": None,
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
            **data,
        }

    def get_motion_data(self, obj_id: int, data: dict[str, Any] = {}) -> dict[str, Any]:
        return {
            "id": obj_id,
            "meeting_id": 1,
            "list_of_speakers_id": 1,
            "state_id": 1,
            "title": "bla",
            "number": "1 - 1",
            "number_value": 1,
            "sequential_number": 2,
            "text": "<p>l&ouml;mk</p>",
            "amendment_paragraphs": {},
            "modified_final_version": "",
            "reason": "",
            "category_weight": 10000,
            "state_extension": "<p>regeer</p>",
            "recommendation_extension": None,
            "sort_weight": 10000,
            "created": 1584512346,
            "last_modified": 1584512346,
            "start_line_number": 1,
            **data,
        }

    def get_mediafile_data(
        self, obj_id: int, data: dict[str, Any] = {}
    ) -> dict[str, Any]:
        file_content = base64.b64encode(b"testtesttest").decode()
        return {
            "id": obj_id,
            "owner_id": "meeting/1",
            "blob": file_content,
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
            **data,
        }

    def test_no_meeting_collection(self) -> None:
        response = self.request(
            "meeting.import",
            {
                "committee_id": 1,
                "meeting": {
                    "meeting": {},
                    "_migration_index": current_migration_index,
                },
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Need exactly one meeting in meeting collection."
            in response.json["message"]
        )

    def test_too_many_meeting_collections(self) -> None:
        response = self.request(
            "meeting.import",
            {
                "committee_id": 1,
                "meeting": {
                    "meeting": {"1": {"id": 1}, "2": {"id": 2}},
                    "_migration_index": current_migration_index,
                },
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Need exactly one meeting in meeting collection."
            in response.json["message"]
        )

    def test_include_organization(self) -> None:
        request_data = self.create_request_data({"organization": {"1": {"id": 1}}})

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert "Invalid collections: organization." in response.json["message"]

    def test_replace_ids_and_write_to_datastore(self) -> None:
        request_data = self.create_request_data(
            {
                "personal_note": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "note": "<p>Some content..</p>",
                        "star": False,
                        "meeting_user_id": 11,
                    }
                },
                "meeting_user": {
                    "11": {
                        "id": 11,
                        "meeting_id": 1,
                        "user_id": 1,
                        "personal_note_ids": [1],
                        "motion_submitter_ids": [],
                        "structure_level_ids": [1],
                        "group_ids": [1],
                    },
                },
                "motion": {
                    "1": self.get_motion_data(
                        1,
                        {
                            "tag_ids": [1],
                            "personal_note_ids": [1],
                        },
                    )
                },
                "list_of_speakers": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "sequential_number": 1,
                        "speaker_ids": [],
                        "projection_ids": [],
                    }
                },
                "tag": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "tagged_ids": ["motion/1"],
                        "name": "testag",
                    }
                },
                "structure_level": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "name": "meeting freak",
                        "meeting_user_ids": [11],
                    },
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["personal_note_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["meeting_user_ids"] = [11]
        request_data["meeting"]["user"]["1"]["meeting_user_ids"] = [11]
        request_data["meeting"]["meeting"]["1"]["motion_ids"] = [1]
        request_data["meeting"]["motion_state"]["1"]["motion_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["list_of_speakers_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["tag_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["structure_level_ids"] = [1]

        start = round(time.time())
        response = self.request("meeting.import", request_data)
        end = round(time.time()) + 1
        self.assert_status_code(response, 200)
        meeting_2 = self.assert_model_exists(
            "meeting/2",
            {
                "name": "Test",
                "description": "blablabla",
                "committee_id": 1,
                "enable_anonymous": False,
                "is_active_in_organization_id": 1,
            },
        )
        assert start <= meeting_2.get("imported_at", 0) <= end
        user_2 = self.assert_model_exists(
            "user/2",
            {
                "username": "test",
                "meeting_ids": [2],
                "committee_ids": [1],
                "meeting_user_ids": [1],
            },
        )
        assert user_2.get("password")
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 2,
                "user_id": 2,
                "structure_level_ids": [1],
                "personal_note_ids": [1],
                "motion_submitter_ids": [],
                "group_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 2, "user_id": 1, "group_ids": [2]}
        )
        self.assert_model_exists("projector/2", {"meeting_id": 2})
        self.assert_model_exists("group/2", {"meeting_user_ids": [1, 2]})
        self.assert_model_exists(
            "personal_note/1",
            {"content_object_id": "motion/2", "meeting_user_id": 1, "meeting_id": 2},
        )
        self.assert_model_exists(
            "tag/1", {"tagged_ids": ["motion/2"], "name": "testag"}
        )
        self.assert_model_exists(
            "structure_level/1", {"meeting_user_ids": [1], "name": "meeting freak"}
        )
        self.assert_model_exists(
            "committee/1", {"user_ids": [2, 1], "meeting_ids": [1, 2]}
        )
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"active_meeting_ids": [1, 2]})

    def test_check_calc_fields(self) -> None:
        request_data = self.create_request_data({})
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"meeting_ids": [2]})
        meeting2 = self.assert_model_exists("meeting/2")
        self.assertCountEqual(meeting2["user_ids"], [1, 2])

    def test_check_usernames_1(self) -> None:
        request_data = self.create_request_data(
            {
                "user": {
                    "11": self.get_user_data(
                        11,
                        {
                            "username": "admin",
                            "meeting_user_ids": [111],
                        },
                    ),
                },
                "meeting_user": {
                    "111": {
                        "id": 111,
                        "meeting_id": 1,
                        "user_id": 11,
                        "group_ids": [1111],
                        "comment": "imported user111 for external meeting1",
                    }
                },
                "group": {
                    "1111": {
                        "id": 1111,
                        "meeting_id": 1,
                        "meeting_user_ids": [111],
                        "admin_group_for_meeting_id": 1,
                        "name": "group1111",
                    }
                },
            }
        )
        del request_data["meeting"]["group"]["1"]
        del request_data["meeting"]["user"]["1"]
        del request_data["meeting"]["meeting_user"]["11"]
        request_data["meeting"]["meeting"]["1"]["admin_group_id"] = 1111
        request_data["meeting"]["meeting"]["1"]["meeting_user_ids"] = [111]
        request_data["meeting"]["meeting"]["1"]["group_ids"] = [2, 1111]
        req_user = request_data["meeting"]["user"]["11"]
        self.set_models(
            {
                "user/1": {
                    fname: req_user.get(fname)
                    for fname in ("username", "email", "first_name", "last_name")
                },
            }
        )
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)

        organization = self.assert_model_exists(ONE_ORGANIZATION_FQID)
        self.assertCountEqual(organization["active_meeting_ids"], [1, 2])

        imported_meeting = self.assert_model_exists(
            "meeting/2",
            {
                "group_ids": [2, 3],
                "committee_id": 1,
                "projector_ids": [2],
                "admin_group_id": 3,
                "default_group_id": 2,
                "motion_state_ids": [1],
                "motion_workflow_ids": [1],
                "is_active_in_organization_id": 1,
            },
        )
        self.assertCountEqual(imported_meeting["user_ids"], [1])

        self.assert_model_exists(
            "user/1",
            {
                "username": "admin",
                "last_name": "Administrator",
                "first_name": "",
                "email": "",
                "meeting_ids": [2],
                "meeting_user_ids": [1],
                "organization_management_level": "superadmin",
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 2,
                "user_id": 1,
                "group_ids": [3],
                "comment": "imported user111 for external meeting1",
            },
        )
        self.assert_model_not_exists("user/2")

        self.assert_model_exists(
            "group/1",
            {
                "meeting_id": 1,
                "name": "group1_m1",
            },
        )
        self.assert_model_exists(
            "group/2",
            {
                "name": "imported default group2",
                "meeting_user_ids": [],
                "meeting_id": 2,
                "default_group_for_meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "group/3",
            {
                "name": "group1111",
                "meeting_user_ids": [1],
                "meeting_id": 2,
                "admin_group_for_meeting_id": 2,
            },
        )

    def test_check_usernames_2(self) -> None:
        self.set_models(
            {
                "user/1": {"username": "admin"},
            }
        )
        request_data = self.create_request_data({})
        request_data["meeting"]["user"]["1"] = self.get_user_data(
            1,
            {
                "username": "admin",
                "last_name": "admin0",
                "meeting_user_ids": [11],
            },
        )
        request_data["meeting"]["user"]["2"] = self.get_user_data(
            2,
            {
                "username": "admin1",
                "last_name": "admin1",
            },
        )

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "username": "admin",
                "last_name": None,
                "meeting_user_ids": [2],
                "meeting_ids": [2],
            },
        )
        self.assert_model_exists(
            "user/2", {"username": "admin1", "last_name": "admin0"}
        )
        self.assert_model_exists(
            "user/3", {"username": "admin11", "last_name": "admin1"}
        )
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 2, "user_id": 2, "group_ids": [2]}
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 2, "user_id": 1, "group_ids": [2]}
        )
        self.assert_model_exists(
            "group/2", {"meeting_user_ids": [1, 2], "meeting_id": 2}
        )

    def test_check_usernames_new_and_twice(self) -> None:
        request_data = self.create_request_data(
            {
                "user": {
                    "1": self.get_user_data(
                        1,
                        {
                            "username": " user new ",
                            "last_name": "new user",
                            "email": "tesT@email.de",
                            "meeting_user_ids": [11],
                        },
                    ),
                },
            }
        )

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)

        self.assert_model_exists(
            "user/2",
            {
                "username": "user new",
                "last_name": "new user",
                "meeting_ids": [2],
                "email": "tesT@email.de",
            },
        )
        request_data["meeting"]["user"]["1"]["email"] = "Test@Email.de"
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "user new",
                "last_name": "new user",
                "meeting_ids": [2, 3],
                "email": "tesT@email.de",
            },
        )
        self.assert_model_not_exists("user/3")

    def test_check_negative_default_vote_weight(self) -> None:
        request_data = self.create_request_data({})
        request_data["meeting"]["user"]["1"] = self.get_user_data(
            1,
            {
                "default_vote_weight": "-1.123456",
            },
        )
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "default_vote_weight must be bigger than or equal to 0.",
            response.json["message"],
        )

    def test_double_import(self) -> None:
        start = round(time.time())
        self.set_models(
            {
                "user/1": {"username": "admin"},
            }
        )
        request_data = self.create_request_data(
            {
                "personal_note": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "note": "<p>Some content..</p>",
                        "star": False,
                        "meeting_user_id": 11,
                    }
                },
                "meeting_user": {
                    "11": {
                        "id": 11,
                        "meeting_id": 1,
                        "user_id": 1,
                        "personal_note_ids": [1],
                        "motion_submitter_ids": [],
                        "group_ids": [1],
                    },
                },
                "motion": {
                    "1": self.get_motion_data(
                        1,
                        {
                            "tag_ids": [1],
                            "personal_note_ids": [1],
                        },
                    )
                },
                "list_of_speakers": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "sequential_number": 1,
                        "speaker_ids": [],
                        "projection_ids": [],
                    }
                },
                "tag": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "tagged_ids": ["motion/1"],
                        "name": "testag",
                    }
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["personal_note_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["meeting_user_ids"] = [11]
        request_data["meeting"]["user"]["1"]["meeting_user_ids"] = [11]
        request_data["meeting"]["meeting"]["1"]["motion_ids"] = [1]
        request_data["meeting"]["motion_state"]["1"]["motion_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["list_of_speakers_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["tag_ids"] = [1]

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1", {"username": "admin", "meeting_user_ids": [2]}
        )
        self.assert_model_exists(
            "user/2", {"username": "test", "meeting_user_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/1",
            {"user_id": 2, "meeting_id": 2, "group_ids": [2], "personal_note_ids": [1]},
        )
        self.assert_model_exists(
            "meeting_user/2", {"user_id": 1, "meeting_id": 2, "group_ids": [2]}
        )
        self.assert_model_exists(
            "group/2",
            {
                "meeting_user_ids": [1, 2],
                "meeting_id": 2,
                "admin_group_for_meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "group/3",
            {
                "meeting_user_ids": [],
                "meeting_id": 2,
                "default_group_for_meeting_id": 2,
            },
        )

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {"username": "admin", "meeting_user_ids": [2, 4], "meeting_ids": [2, 3]},
        )
        self.assert_model_exists(
            "user/2",
            {
                "username": "test",
                "meeting_user_ids": [1, 3],
                "meeting_ids": [2, 3],
                "committee_ids": [1],
            },
        )

        self.assert_model_exists(
            "meeting_user/3",
            {"user_id": 2, "meeting_id": 3, "group_ids": [4], "personal_note_ids": [2]},
        )
        self.assert_model_exists(
            "meeting_user/4", {"user_id": 1, "meeting_id": 3, "group_ids": [4]}
        )
        meeting_3 = self.assert_model_exists(
            "meeting/3",
            {
                "name": "Test",
                "description": "blablabla",
                "committee_id": 1,
                "enable_anonymous": False,
                "user_ids": [2, 1],
                "group_ids": [4, 5],
                "meeting_user_ids": [3, 4],
            },
        )
        assert start <= meeting_3.get("imported_at", 0) <= start + 300
        self.assert_model_exists("projector/3", {"meeting_id": 3})
        self.assert_model_exists(
            "group/4",
            {
                "meeting_user_ids": [3, 4],
                "meeting_id": 3,
                "admin_group_for_meeting_id": 3,
            },
        )
        self.assert_model_exists(
            "group/5",
            {
                "name": "imported default group2",
                "meeting_user_ids": [],
                "meeting_id": 3,
                "default_group_for_meeting_id": 3,
            },
        )
        self.assert_model_exists(
            "personal_note/2", {"content_object_id": "motion/3", "meeting_id": 3}
        )
        self.assert_model_exists(
            "tag/2", {"tagged_ids": ["motion/3"], "name": "testag", "meeting_id": 3}
        )
        self.assert_model_exists(
            "committee/1", {"user_ids": [2, 1], "meeting_ids": [1, 2, 3]}
        )

    def test_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "admin",
                    "organization_management_level": "can_manage_users",
                },
            }
        )
        response = self.request("meeting.import", self.create_request_data({}))
        self.assert_status_code(response, 403)
        assert (
            "Missing permission: CommitteeManagementLevel can_manage in committee 1"
            in response.json["message"]
        )

    def test_use_blobs(self) -> None:
        file_content = base64.b64encode(b"testtesttest").decode()
        request_data = self.create_request_data(
            {
                "mediafile": {"1": self.get_mediafile_data(1)},
            }
        )
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [1]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        mediafile = self.get_model("mediafile/1")
        assert mediafile.get("blob") is None
        self.media.upload_mediafile.assert_called_with(file_content, 1, "text/plain")

    def test_inherited_access_group_ids_none(self) -> None:
        request_data = self.create_request_data(
            {
                "mediafile": {
                    "1": self.get_mediafile_data(
                        1,
                        {
                            "access_group_ids": None,
                            "inherited_access_group_ids": None,
                        },
                    ),
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [1]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)

    def test_inherited_access_group_ids_wrong_order(self) -> None:
        request_data = self.create_request_data(
            {
                "group": {
                    "1": self.get_group_data(
                        1,
                        {
                            "admin_group_for_meeting_id": 1,
                            "mediafile_access_group_ids": [1],
                            "mediafile_inherited_access_group_ids": [1],
                            "meeting_user_ids": [11],
                        },
                    ),
                    "2": self.get_group_data(
                        2,
                        {
                            "default_group_for_meeting_id": 1,
                            "mediafile_access_group_ids": [1],
                            "mediafile_inherited_access_group_ids": [1],
                        },
                    ),
                },
                "mediafile": {
                    "1": self.get_mediafile_data(
                        1,
                        {
                            "is_public": False,
                            "access_group_ids": [1, 2],
                            "inherited_access_group_ids": [1, 2],
                        },
                    ),
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["group_ids"] = [1, 2]

        # try both orders, both should work
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        # other order
        request_data["meeting"]["mediafile"]["1"]["inherited_access_group_ids"] = [2, 1]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)

    def test_meeting_user_ids(self) -> None:
        # Calculated field.
        # User/1 is in user_ids, because calling user is added
        response = self.request("meeting.import", self.create_request_data({}))
        self.assert_status_code(response, 200)
        # XXX meeting2 = self.assert_model_exists("meeting/2")
        # XXX self.assertCountEqual(meeting2["user_ids"], [1, 2])
        # self.assert_model_exists("user/2", {"username": "test", "meeting_ids": [2]})
        organization = self.assert_model_exists("organization/1")
        self.assertCountEqual(organization.get("user_ids", []), [1, 2])

    def test_motion_recommendation_extension(self) -> None:
        # Special field
        request_data = self.create_request_data(
            {
                "motion": {
                    "1": self.get_motion_data(
                        1,
                        {
                            "referenced_in_motion_state_extension_ids": [2],
                            "referenced_in_motion_recommendation_extension_ids": [2],
                        },
                    ),
                    "2": self.get_motion_data(
                        2,
                        {
                            "list_of_speakers_id": 2,
                            "state_extension": "bla[motion/1]bla",
                            "state_extension_reference_ids": ["motion/1"],
                            "recommendation_extension": "bla[motion/1]bla",
                            "recommendation_extension_reference_ids": ["motion/1"],
                        },
                    ),
                },
                "list_of_speakers": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "sequential_number": 1,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                    "2": {
                        "id": 2,
                        "meeting_id": 1,
                        "content_object_id": "motion/2",
                        "closed": False,
                        "sequential_number": 2,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["motion_ids"] = [1, 2]
        request_data["meeting"]["meeting"]["1"]["list_of_speakers_ids"] = [1, 2]
        request_data["meeting"]["motion_state"]["1"]["motion_ids"] = [1, 2]

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/3",
            {
                "state_extension": "bla[motion/2]bla",
                "state_extension_reference_ids": ["motion/2"],
                "recommendation_extension": "bla[motion/2]bla",
                "recommendation_extension_reference_ids": ["motion/2"],
            },
        )

    def test_motion_recommendation_extension_missing_model(self) -> None:
        # Special field
        request_data = self.create_request_data(
            {
                "motion": {
                    "1": self.get_motion_data(1),
                    "2": self.get_motion_data(
                        2,
                        {
                            "id": 2,
                            "list_of_speakers_id": 2,
                            "recommendation_extension": "bla[motion/11]bla",
                        },
                    ),
                },
                "list_of_speakers": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                    "2": {
                        "id": 2,
                        "meeting_id": 1,
                        "content_object_id": "motion/2",
                        "closed": False,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["motion_ids"] = [1, 2]
        request_data["meeting"]["meeting"]["1"]["list_of_speakers_ids"] = [1, 2]
        request_data["meeting"]["motion_state"]["1"]["motion_ids"] = [1, 2]

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "Found motion/11 in recommendation_extension but not in models."
            in response.json["message"]
        )

    def test_logo_id(self) -> None:
        # Template Relation Field
        request_data = self.create_request_data(
            {
                "mediafile": {
                    "3": self.get_mediafile_data(
                        3,
                        {
                            "used_as_logo_web_header_in_meeting_id": 1,
                        },
                    )
                }
            }
        )
        request_data["meeting"]["meeting"]["1"]["logo_web_header_id"] = 3
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [3]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/1")
        self.assert_model_exists("meeting/2", {"logo_web_header_id": 1})

    def test_font_italic_id(self) -> None:
        # Template Relation Field
        request_data = self.create_request_data(
            {
                "mediafile": {
                    "3": self.get_mediafile_data(
                        3,
                        {
                            "used_as_font_italic_in_meeting_id": 1,
                        },
                    )
                }
            }
        )
        request_data["meeting"]["meeting"]["1"]["font_italic_id"] = 3
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [3]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/1")
        self.assert_model_exists("meeting/2", {"font_italic_id": 1})

    def test_logo_id_wrong_place(self) -> None:
        # Template Relation Field
        request_data = self.create_request_data(
            {
                "mediafile": {
                    "3": self.get_mediafile_data(
                        3,
                        {
                            "used_as_logo_web_in_meeting_id": 1,
                        },
                    )
                }
            }
        )
        request_data["meeting"]["meeting"]["1"]["logo_web_id"] = 3
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [3]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "\tmeeting/1: Invalid fields logo_web_id (value: 3)\n\tmediafile/3: Invalid fields used_as_logo_web_in_meeting_id (value: 1)"
            in response.json["message"]
        )

    def test_is_public_error(self) -> None:
        request_data = self.create_request_data(
            {
                "mediafile": {
                    "3": self.get_mediafile_data(
                        3,
                        {
                            "used_as_logo_web_header_in_meeting_id": 1,
                            "parent_id": 2,
                        },
                    ),
                    "2": self.get_mediafile_data(
                        2,
                        {
                            "title": "dir",
                            "is_directory": True,
                            "filesize": 0,
                            "filename": None,
                            "mimetype": None,
                            "is_public": False,
                            "child_ids": [3],
                        },
                    ),
                }
            }
        )
        request_data["meeting"]["meeting"]["1"]["logo_web_header_id"] = 3
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [2, 3]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert "mediafile/3: is_public is wrong." in response.json["message"]

    def test_request_user_in_admin_group(self) -> None:
        response = self.request("meeting.import", self.create_request_data({}))
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1", {"meeting_user_ids": [2], "username": "admin"}
        )
        self.assert_model_exists(
            "meeting_user/2", {"group_ids": [2], "meeting_id": 2, "user_id": 1}
        )
        self.assert_model_exists(
            "user/2", {"meeting_user_ids": [1], "username": "test"}
        )
        self.assert_model_exists(
            "meeting_user/1", {"group_ids": [2], "meeting_id": 2, "user_id": 2}
        )
        self.assert_model_exists("meeting/2", {"user_ids": [2, 1]})
        self.assert_model_exists(
            "group/2",
            {
                "meeting_user_ids": [1, 2],
                "meeting_id": 2,
                "name": "imported admin group1",
            },
        )

    def test_motion_all_derived_motion_ids(self) -> None:
        """
        repair and fields_to_remove delete the motion forwarding fields
        (all_)origin_id and (all_)derived_motion_ids. Otherwise the meeting
        couldn't be imported with relations to other meeting.
        """
        request_data = self.create_request_data(
            {
                "motion": {
                    "1": self.get_motion_data(
                        1,
                        {
                            "all_derived_motion_ids": [1],
                            "list_of_speakers_id": 1,
                            "state_id": 1,
                        },
                    ),
                },
                "list_of_speakers": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "sequential_number": 1,
                        "speaker_ids": [],
                        "projection_ids": [],
                    }
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["motion_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["list_of_speakers_ids"] = [1]
        request_data["meeting"]["motion_state"]["1"]["motion_ids"] = [1]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {
                "meeting_id": 2,
                "origin_id": None,
                "derived_motion_ids": None,
                "all_origin_ids": None,
                "all_derived_motion_ids": None,
            },
        )

    def test_motion_all_origin_ids(self) -> None:
        request_data = self.create_request_data(
            {
                "motion": {
                    "1": self.get_motion_data(
                        1,
                        {
                            "all_origin_ids": [2],
                            "list_of_speakers_id": 1,
                            "state_id": 1,
                        },
                    ),
                    "2": self.get_motion_data(
                        2,
                        {
                            "all_derived_motion_ids": [1],
                            "list_of_speakers_id": 2,
                            "state_id": 1,
                        },
                    ),
                },
                "list_of_speakers": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "sequential_number": 1,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                    "2": {
                        "id": 2,
                        "meeting_id": 1,
                        "content_object_id": "motion/2",
                        "closed": False,
                        "sequential_number": 1,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["motion_ids"] = [1, 2]
        request_data["meeting"]["meeting"]["1"]["list_of_speakers_ids"] = [1, 2]
        request_data["meeting"]["motion_state"]["1"]["motion_ids"] = [1, 2]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "Motion all_origin_ids and all_derived_motion_ids should be empty."
            in response.json["message"]
        )

    def test_missing_required_field(self) -> None:
        request_data = self.create_request_data(
            {
                "motion": {
                    "1": self.get_motion_data(
                        1,
                        {
                            "all_origin_ids": [],
                            "list_of_speakers_id": None,
                            "state_id": 1,
                        },
                    ),
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["motion_ids"] = [1]
        request_data["meeting"]["motion_state"]["1"]["motion_ids"] = [1]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "motion/1/list_of_speakers_id: Field required but empty."
            in response.json["message"]
        )

    def test_field_check(self) -> None:
        request_data = self.create_request_data(
            {
                "mediafile": {
                    "1": self.get_mediafile_data(
                        1,
                        {
                            "foobar": "test this",
                        },
                    ),
                }
            }
        )
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "mediafile/1: Invalid fields foobar (value: test this)"
            in response.json["message"]
        )

    def test_dont_import_action_worker(self) -> None:
        request_data = self.create_request_data(
            {
                "action_worker": {
                    "1": {
                        "id": 1,
                        "name": "testcase",
                        "state": ActionWorkerState.END,
                        "created": round(time.time() - 3),
                        "timestamp": round(time.time()),
                    }
                }
            }
        )
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("action_worker/1")

    def test_dont_import_import_preview(self) -> None:
        request_data = self.create_request_data(
            {
                "import_preview": {
                    "1": {
                        "id": 1,
                        "name": "testcase",
                        "state": "done",
                        "created": round(time.time() - 3),
                    }
                }
            }
        )
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("import_preview/1")

    def test_bad_format_invalid_id_key(self) -> None:
        request_data = self.create_request_data({"tag": {"1": {"id": 2}}})
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert "tag/1: Id must be the same as model['id']" in response.json["message"]

    def test_limit_of_meetings_error(self) -> None:
        self.update_model(ONE_ORGANIZATION_FQID, {"limit_of_meetings": 1})
        response = self.request("meeting.import", self.create_request_data({}))
        self.assert_status_code(response, 400)
        self.assertIn(
            "You cannot import an active meeting, because you reached your limit of 1 active meetings.",
            response.json["message"],
        )

    def test_limit_of_meetings_ok(self) -> None:
        self.update_model(ONE_ORGANIZATION_FQID, {"limit_of_meetings": 2})
        response = self.request("meeting.import", self.create_request_data({}))
        self.assert_status_code(response, 200)

    def test_check_limit_of_users_okay(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 2},
            }
        )
        request_data = self.create_request_data({})
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2")

    def test_check_limit_of_users_okay_merged_user(self) -> None:
        self.set_models({ONE_ORGANIZATION_FQID: {"limit_of_users": 1}})
        self.assert_model_exists(
            "user/1",
            {"username": "admin", "first_name": None, "last_name": None, "email": None},
        )
        request_data = self.create_request_data({})
        request_data["meeting"]["user"]["1"]["username"] = "admin"
        request_data["meeting"]["user"]["1"]["first_name"] = None
        request_data["meeting"]["user"]["1"]["last_name"] = None
        request_data["meeting"]["user"]["1"]["email"] = None
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"username": "admin"})
        self.assert_model_not_exists("user/2")

    def test_check_hit_limit_of_users(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 2},
                "user/2": {"username": "test2", "is_active": True},
            }
        )
        request_data = self.create_request_data({})
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "The number of active users cannot exceed the limit of users."
            == response.json["message"]
        )

    def test_merge_users_check_committee_and_meeting(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "user_ids": [1, 14],
                },
                "committee/2": {
                    "name": "Committee for imported meeting",
                },
                "meeting/1": {
                    "user_ids": [1, 14],
                    "meeting_user_ids": [1, 14],
                },
                "group/1": {
                    "meeting_user_ids": [1, 14],
                },
                "user/1": {
                    "meeting_ids": [1],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [1],
                },
                "user/14": {
                    "username": "username_to_merge",
                    "first_name": None,
                    "last_name": None,
                    "email": "test@example.de",
                    "meeting_user_ids": [14],
                    "meeting_ids": [1],
                    "committee_ids": [1],
                    "organization_id": 1,
                },
                "meeting_user/14": {
                    "meeting_id": 1,
                    "user_id": 14,
                    "group_ids": [1],
                },
                "organization/1": {"user_ids": [1, 14], "committee_ids": [1, 2]},
            }
        )
        request_data = self.create_request_data(
            {
                "user": {
                    "12": {
                        "id": 12,
                        "username": "username_to_merge",
                        "email": "test@example.de",
                        "meeting_user_ids": [12],
                        "organization_id": 1,
                    },
                    "13": {
                        "id": 13,
                        "username": "username_import13",
                        "email": "test_new@example.de",
                        "meeting_user_ids": [13],
                        "organization_id": 1,
                    },
                },
                "meeting_user": {
                    "12": {
                        "id": 12,
                        "meeting_id": 1,
                        "user_id": 12,
                        "group_ids": [2],
                    },
                    "13": {
                        "id": 13,
                        "meeting_id": 1,
                        "user_id": 13,
                        "group_ids": [2],
                    },
                },
            }
        )
        request_data["meeting"]["group"]["1"]["meeting_user_ids"] = [11]
        request_data["meeting"]["group"]["2"]["meeting_user_ids"] = [12, 13]
        request_data["meeting"]["meeting"]["1"]["meeting_user_ids"] = [11, 12, 13]
        request_data["meeting"]["meeting"]["1"]["user_ids"] = [1, 12, 13]
        request_data["meeting"]["user"]["1"]["username"] = "username_import1"
        request_data["committee_id"] = 2
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["number_of_imported_users"] == 3
        assert response.json["results"][0][0]["number_of_merged_users"] == 1
        self.assert_model_exists(
            "user/1",
            {
                "username": "admin",
                "meeting_ids": [1, 2],
                "committee_ids": [1, 2],
                "meeting_user_ids": [1, 18],
            },
        )
        self.assert_model_exists(
            "user/14",
            {
                "username": "username_to_merge",
                "meeting_ids": [1, 2],
                "committee_ids": [1, 2],
                "meeting_user_ids": [14, 16],
            },
        )
        self.assert_model_exists(
            "user/15",
            {
                "username": "username_import1",
                "meeting_ids": [2],
                "committee_ids": [2],
                "meeting_user_ids": [15],
            },
        )
        self.assert_model_exists(
            "user/16",
            {
                "username": "username_import13",
                "meeting_ids": [2],
                "committee_ids": [2],
                "meeting_user_ids": [17],
            },
        )
        committee1 = self.assert_model_exists("committee/1", {"meeting_ids": [1]})
        assert sorted(committee1.get("user_ids", [])) == [1, 14]
        meeting1 = self.assert_model_exists("meeting/1", {"committee_id": 1})
        assert sorted(meeting1.get("user_ids", [])) == [1, 14]
        assert sorted(meeting1.get("meeting_user_ids", [])) == [1, 14]
        self.assert_model_exists("committee/2", {"meeting_ids": [2]})
        self.assert_model_exists("meeting/2", {"committee_id": 2})
        organization = self.assert_model_exists(
            "organization/1", {"committee_ids": [1, 2], "active_meeting_ids": [1, 2]}
        )
        assert sorted(organization.get("user_ids", [])) == [1, 14, 15, 16]

    def test_merge_users_check_user_meeting_ids(self) -> None:
        self.set_models(
            {
                "user/14": {
                    "username": "username_test",
                    "first_name": None,
                    "last_name": None,
                    "email": "test@example.de",
                    "meeting_ids": [1],
                    "meeting_user_ids": [14],
                    "organization_id": 1,
                },
                "meeting_user/14": {
                    "meeting_id": 1,
                    "user_id": 14,
                    "group_ids": [1],
                },
                "group/1": {
                    "meeting_user_ids": [14],
                },
                "meeting/1": {
                    "user_ids": [14],
                },
                "organization/1": {"user_ids": [1, 14]},
            }
        )
        request_data = self.create_request_data(
            {
                "user": {
                    "12": {
                        "id": 12,
                        "username": "username_test",
                        "email": "test@example.de",
                        "meeting_ids": [1],
                        "organization_id": 1,
                        "meeting_user_ids": [12],
                    },
                },
                "meeting_user": {
                    "12": {
                        "id": 12,
                        "meeting_id": 1,
                        "user_id": 12,
                        "group_ids": [1],
                    },
                },
            }
        )
        request_data["meeting"]["group"]["1"]["meeting_user_ids"] = [11, 12]
        request_data["meeting"]["meeting"]["1"]["meeting_user_ids"] = [11, 12]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["number_of_imported_users"] == 2
        assert response.json["results"][0][0]["number_of_merged_users"] == 1
        self.assert_model_exists(
            "committee/1", {"meeting_ids": [1, 2], "user_ids": [15, 14, 1]}
        )
        meeting2 = self.assert_model_exists("meeting/2", {"committee_id": 1})
        assert sorted(meeting2.get("user_ids", [])) == [1, 14, 15]
        self.assert_model_exists("meeting/1", {"user_ids": [14]})
        self.assert_model_exists("user/1", {"username": "admin", "meeting_ids": [2]})
        self.assert_model_exists(
            "user/14", {"username": "username_test", "meeting_ids": [1, 2]}
        )

    def test_merge_users_relation_field(self) -> None:
        self.set_models(
            {
                "user/14": {
                    "username": "username_test",
                    "first_name": None,
                    "last_name": None,
                    "email": "test@example.de",
                    "is_present_in_meeting_ids": [1],  # Relation Field
                    "organization_id": 1,
                },
                "meeting/1": {
                    "present_user_ids": [14],
                },
                "organization/1": {"user_ids": [1, 14]},
            }
        )
        request_data = self.create_request_data(
            {
                "user": {
                    "12": {
                        "id": 12,
                        "username": "username_test",
                        "first_name": None,
                        "last_name": None,
                        "email": "test@example.de",
                        "is_present_in_meeting_ids": [1],
                        "organization_id": 1,
                    },
                    "13": {
                        "id": 13,
                        "username": "test_new_user",
                        "first_name": None,
                        "last_name": None,
                        "email": "test_new@example.de",
                        "is_present_in_meeting_ids": [1],
                        "organization_id": 1,
                    },
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["present_user_ids"] = [12, 13]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        user14 = self.assert_model_exists("user/14", {"username": "username_test"})
        assert user14.get("is_present_in_meeting_ids") == [1, 2]
        user16 = self.assert_model_exists("user/16", {"username": "test_new_user"})
        assert user16.get("is_present_in_meeting_ids") == [2]
        self.assert_model_exists("meeting/2", {"present_user_ids": [14, 16]})

    def test_is_present_existing_user(self) -> None:
        self.set_models(
            {
                "user/14": {
                    "username": "test",
                    "last_name": "Administrator",
                    "organization_id": 1,
                },
                "organization/1": {"user_ids": [14]},
            }
        )
        request_data = self.create_request_data()
        request_data["meeting"]["meeting"]["1"]["present_user_ids"] = [1]
        request_data["meeting"]["user"]["1"]["is_present_in_meeting_ids"] = [1]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/14", {"username": "test", "is_present_in_meeting_ids": [2]}
        )
        self.assert_model_exists("meeting/2", {"present_user_ids": [14]})

    def test_is_present_new_user(self) -> None:
        self.set_models(
            {
                "user/14": {
                    "username": "test",
                    "organization_id": 1,
                },
                "organization/1": {"user_ids": [14]},
            }
        )
        request_data = self.create_request_data()
        request_data["meeting"]["meeting"]["1"]["present_user_ids"] = [1]
        request_data["meeting"]["user"]["1"]["is_present_in_meeting_ids"] = [1]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/15", {"username": "test1", "is_present_in_meeting_ids": [2]}
        )
        self.assert_model_exists("meeting/2", {"present_user_ids": [15]})

    def test_with_default_password(self) -> None:
        request_data = self.create_request_data()
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        user = self.get_model("user/2")
        assert user["default_password"] != "admin"
        assert self.auth.is_equal(user["default_password"], user["password"])

    def test_without_default_password(self) -> None:
        request_data = self.create_request_data()
        request_data["meeting"]["user"]["1"]["default_password"] = ""
        request_data["meeting"]["user"]["1"]["last_email_sent"] = int(time.time())
        request_data["meeting"]["user"]["1"]["last_login"] = int(time.time())
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        user = self.get_model("user/2")
        assert len(user["default_password"]) == 10
        assert self.auth.is_equal(user["default_password"], user["password"])
        assert "last_email_sent" not in user
        assert "last_login" not in user

    def test_merge_meeting_users_fields(self) -> None:
        self.set_models(
            {
                "user/14": {
                    "username": "username_test",
                    "first_name": None,
                    "last_name": None,
                    "email": "test@example.de",
                    "meeting_user_ids": [14],
                    "organization_id": 1,
                },
                "meeting_user/14": {
                    "meeting_id": 1,
                    "user_id": 14,
                    "personal_note_ids": [1],
                    "motion_submitter_ids": [],
                    "vote_delegated_to_id": 1,
                },
                "personal_note/1": {
                    "meeting_id": 1,
                    "content_object_id": None,
                    "note": "<p>Some content..</p>",
                    "star": False,
                    "meeting_user_id": 14,
                },
                "meeting/1": {
                    "personal_note_ids": [1],
                    "meeting_user_ids": [14],
                },
            }
        )
        request_data = self.create_request_data(
            {
                "user": {
                    "12": {
                        "id": 12,
                        "username": "username_test",
                        "first_name": None,
                        "last_name": None,
                        "email": "test@example.de",
                        "meeting_user_ids": [12],
                        "organization_id": 1,
                    },
                    "13": {
                        "id": 13,
                        "username": "test_new_user",
                        "first_name": None,
                        "last_name": None,
                        "email": "test_new@example.de",
                        "meeting_user_ids": [13],
                        "organization_id": 1,
                    },
                },
                "personal_note": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": None,
                        "note": "<p>Some content..</p>",
                        "star": False,
                        "meeting_user_id": 12,
                    },
                    "2": {
                        "id": 2,
                        "meeting_id": 1,
                        "content_object_id": None,
                        "note": "blablabla",
                        "star": False,
                        "meeting_user_id": 13,
                    },
                },
                "meeting_user": {
                    "12": {
                        "id": 12,
                        "meeting_id": 1,
                        "user_id": 12,
                        "personal_note_ids": [1],
                        "motion_submitter_ids": [],
                        "vote_delegated_to_id": 13,
                    },
                    "13": {
                        "id": 13,
                        "meeting_id": 1,
                        "user_id": 13,
                        "personal_note_ids": [2],
                        "motion_submitter_ids": [],
                        "vote_delegations_from_ids": [12],
                    },
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["personal_note_ids"] = [1, 2]
        request_data["meeting"]["meeting"]["1"]["meeting_user_ids"] = [11, 12, 13]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/16",
            {
                "username": "test_new_user",
                "meeting_user_ids": [17],
            },
        )
        self.assert_model_exists(
            "meeting_user/17",
            {"user_id": 16, "meeting_id": 2, "personal_note_ids": [3]},
        )
        self.assert_model_exists(
            "user/14",
            {
                "username": "username_test",
                "organization_id": 1,
                "meeting_user_ids": [14, 16],
            },
        )
        self.assert_model_exists(
            "meeting_user/14",
            {"user_id": 14, "meeting_id": 1, "personal_note_ids": [1]},
        )
        self.assert_model_exists(
            "meeting_user/16",
            {"user_id": 14, "meeting_id": 2, "personal_note_ids": [2]},
        )

    def test_check_forbidden_fields(self) -> None:
        request_data = self.create_request_data(
            {
                "user": {
                    "14": {
                        "id": 14,
                        "username": "user14",
                        "organization_management_level": "superadmin",
                        "committee_management_ids": [1],
                        "organization_id": 1,
                    }
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["organization_tag_ids"] = [1, 2, 3]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/2", {"organization_tag_ids": None})
        self.assert_model_exists(
            "user/3",
            {
                "id": 3,
                "username": "user14",
                "organization_management_level": None,
                "committee_management_ids": None,
                "organization_id": 1,
            },
        )

    def test_check_missing_admin_group_in_meeting(self) -> None:
        self.set_models(
            {
                "user/1": {"username": "admin"},
            }
        )
        request_data = self.create_request_data({})
        request_data["meeting"]["meeting"]["1"]["admin_group_id"] = None
        request_data["meeting"]["group"]["1"]["admin_group_for_meeting_id"] = None

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "Imported meeting has no AdminGroup to assign to request user",
            response.json["message"],
        )

    def test_with_listfields_from_migration(self) -> None:
        """test for listFields in event.data after migration. Uses migration 0035 to create one"""
        data = self.create_request_data(
            {
                "motion": {
                    "5": self.get_motion_data(
                        5,
                        {
                            "title": "motion/5",
                            "referenced_in_motion_state_extension_ids": [],
                        },
                    ),
                    "6": self.get_motion_data(
                        6,
                        {
                            "title": "motion/6",
                            "state_extension": "[motion/5]",
                            "list_of_speakers_id": 2,
                        },
                    ),
                },
                "list_of_speakers": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/5",
                        "closed": False,
                        "sequential_number": 1,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                    "2": {
                        "id": 2,
                        "meeting_id": 1,
                        "content_object_id": "motion/6",
                        "closed": False,
                        "sequential_number": 2,
                        "speaker_ids": [],
                        "projection_ids": [],
                    },
                },
            }
        )
        data["meeting"]["meeting"]["1"]["motion_ids"] = [5, 6]
        data["meeting"]["meeting"]["1"]["list_of_speakers_ids"] = [1, 2]
        data["meeting"]["motion_state"]["1"]["motion_ids"] = [5, 6]
        data["meeting"]["_migration_index"] = 35
        assert (
            data["meeting"]["motion"]["5"]["referenced_in_motion_state_extension_ids"]
            == []
        )

        response = self.request("meeting.import", data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {"title": "motion/5", "referenced_in_motion_state_extension_ids": [3]},
        )
        self.assert_model_exists(
            "motion/3", {"title": "motion/6", "state_extension": "[motion/2]"}
        )

    def test_without_migration_index(self) -> None:
        data = self.create_request_data({})
        del data["meeting"]["_migration_index"]
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.meeting must contain ['_migration_index'] properties",
            response.json["message"],
        )

    def test_with_negative_migration_index(self) -> None:
        data = self.create_request_data({})
        data["meeting"]["_migration_index"] = -1
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.meeting._migration_index must be bigger than or equal to 1",
            response.json["message"],
        )

    def test_with_migration_index_to_high(self) -> None:
        data = self.create_request_data({})
        data["meeting"]["_migration_index"] = 12345678
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 400)
        self.assertIn(
            f"Your data migration index '12345678' is higher than the migration index of this backend '{current_migration_index}'! Please, update your backend!",
            response.json["message"],
        )

    def test_all_migrations(self) -> None:
        data = self.create_request_data({})
        data["meeting"]["_migration_index"] = 1
        del data["meeting"]["user"]["1"]["organization_id"]
        data["meeting"]["meeting"]["1"]["motion_poll_default_100_percent_base"] = "Y"
        data["meeting"]["meeting"]["1"][
            "assignment_poll_default_100_percent_base"
        ] = "YN"
        data["meeting"]["meeting"]["1"]["poll_default_100_percent_base"] = "YNA"

        with CountDatastoreCalls(verbose=True) as counter:
            response = self.request("meeting.import", data)
        self.assert_status_code(response, 200)
        assert counter.calls == 5
        self.assert_model_exists("user/1", {"meeting_user_ids": [2]})
        self.assert_model_exists(
            "meeting_user/2", {"user_id": 1, "meeting_id": 2, "group_ids": [2]}
        )
        meeting = self.assert_model_exists(
            "meeting/2",
            {
                "assignment_poll_enable_max_votes_per_option": False,
                "motion_poll_default_onehundred_percent_base": "Y",
                "assignment_poll_default_onehundred_percent_base": "YN",
                "poll_default_onehundred_percent_base": "YNA",
            },
        )  # checker repair
        self.assertCountEqual(meeting["user_ids"], [1, 2])
        group2 = self.assert_model_exists("group/2")
        self.assertCountEqual(group2["meeting_user_ids"], [1, 2])
        committee1 = self.get_model("committee/1")
        self.assertCountEqual(committee1["user_ids"], [1, 2])
        self.assertCountEqual(committee1["meeting_ids"], [1, 2])
        self.assert_model_exists("motion_workflow/1", {"sequential_number": 1})
        self.assert_model_exists("projector/2", {"sequential_number": 1})
        self.assert_model_exists(
            "organization/1", {"user_ids": [1, 2], "active_meeting_ids": [1, 2]}
        )

    @performance
    def test_big_file(self) -> None:
        data = {
            "meeting": get_initial_data_file("global/data/put_your_file.json"),
            "committee_id": 1,
        }
        with Profiler("test_meeting_import.prof"):
            response = self.request("meeting.import", data)
        self.assert_status_code(response, 200)

    def test_import_amendment_paragraphs(self) -> None:
        request_data = self.create_request_data(
            {
                "motion": {
                    "1": self.get_motion_data(
                        1,
                        {},
                    )
                },
                "list_of_speakers": {
                    "1": {
                        "id": 1,
                        "meeting_id": 1,
                        "content_object_id": "motion/1",
                        "closed": False,
                        "sequential_number": 1,
                        "speaker_ids": [],
                        "projection_ids": [],
                    }
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["motion_ids"] = [1]
        request_data["meeting"]["motion_state"]["1"]["motion_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["list_of_speakers_ids"] = [1]
        request_data["meeting"]["motion"]["1"]["amendment_paragraphs"] = {
            "0": None,
            "1": "<it>test</it>",
            "2": "</>broken",
        }
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {"amendment_paragraphs": {"1": "&lt;it&gt;test&lt;/it&gt;", "2": "broken"}},
        )

    def test_import_with_wrong_decimal(self) -> None:
        data = self.create_request_data({})
        data["meeting"]["user"]["1"]["default_vote_weight"] = "1A0"
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 400)
        assert (
            "user/1/default_vote_weight: Type error: Type is not <openslides_backend.models.fields.DecimalField"
            in response.json["message"]
        )

    def test_import_new_user_with_vote(self) -> None:
        self.set_models(
            {
                "vote/1": {
                    "user_id": 1,
                    "delegated_user_id": 1,
                    "meeting_id": 1,
                    "option_id": 10,
                    "user_token": "asdfgh",
                },
                "option/10": {
                    "vote_ids": [1],
                    "meeting_id": 1,
                },
                "user/1": {
                    "vote_ids": [1],
                    "delegated_vote_ids": [1],
                },
            }
        )
        data = self.create_request_data(
            {
                "vote": {
                    "1": {
                        "id": 1,
                        "user_id": 1,
                        "delegated_user_id": 1,
                        "meeting_id": 1,
                        "option_id": 1,
                        "user_token": "asdfgh",
                    },
                },
                "option": {
                    "1": {
                        "id": 1,
                        "vote_ids": [1],
                        "meeting_id": 1,
                    },
                },
            }
        )
        data["meeting"]["meeting"]["1"]["vote_ids"] = [1]
        data["meeting"]["meeting"]["1"]["option_ids"] = [1]
        data["meeting"]["user"]["1"]["vote_ids"] = [1]
        data["meeting"]["user"]["1"]["delegated_vote_ids"] = [1]
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "username": "admin",
                "meeting_user_ids": [2],
                "vote_ids": [1],
                "delegated_vote_ids": [1],
            },
        )
        self.assert_model_exists(
            "user/2",
            {
                "username": "test",
                "vote_ids": [2],
                "delegated_vote_ids": [2],
                "meeting_user_ids": [1],
            },
        )

    def test_import_existing_user_with_vote(self) -> None:
        self.set_models(
            {
                "vote/1": {
                    "user_id": 1,
                    "delegated_user_id": 1,
                    "meeting_id": 1,
                    "option_id": 10,
                    "user_token": "asdfgh",
                },
                "option/10": {
                    "vote_ids": [1],
                    "meeting_id": 1,
                },
                "user/1": {
                    "vote_ids": [1],
                    "delegated_vote_ids": [1],
                },
            }
        )
        data = self.create_request_data(
            {
                "vote": {
                    "1": {
                        "id": 1,
                        "user_id": 1,
                        "delegated_user_id": 1,
                        "meeting_id": 1,
                        "option_id": 1,
                        "user_token": "asdfgh",
                    },
                },
                "option": {
                    "1": {
                        "id": 1,
                        "vote_ids": [1],
                        "meeting_id": 1,
                    },
                },
            }
        )
        data["meeting"]["meeting"]["1"]["vote_ids"] = [1]
        data["meeting"]["meeting"]["1"]["option_ids"] = [1]
        data["meeting"]["user"]["1"]["username"] = "admin"
        data["meeting"]["user"]["1"]["last_name"] = ""
        data["meeting"]["user"]["1"]["vote_ids"] = [1]
        data["meeting"]["user"]["1"]["delegated_vote_ids"] = [1]
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "username": "admin",
                "meeting_user_ids": [1],
                "vote_ids": [1, 2],
                "delegated_vote_ids": [1, 2],
            },
        )
        self.assert_model_not_exists("user/2")

    def test_without_users(self) -> None:
        data = self.create_request_data()
        meeting_data = data["meeting"]
        del meeting_data["meeting"]["1"]["meeting_user_ids"]
        del meeting_data["group"]["1"]["meeting_user_ids"]
        del meeting_data["user"]
        del meeting_data["meeting_user"]
        self.assert_model_not_exists("meeting_user/1")
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "username": "admin",
                "meeting_user_ids": [1],
            },
        )
        self.assert_model_not_exists("user/2")
