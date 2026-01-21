import base64
import time
from copy import deepcopy
from typing import Any

import pytest
from psycopg.types.json import Jsonb

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.http.views.presenter_view import PresenterView
from openslides_backend.models.models import Meeting
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, get_initial_data_file
from tests.system.action.base import BaseActionTestCase
from tests.system.util import (
    Profiler,
    create_presenter_test_application,
    get_route_path,
    performance,
)
from tests.util import Client

MIG_INDEX = 100


# @pytest.mark.skip(reason="Requires initial migration. TODO: unskip once it is added.")
class MeetingImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1, {"external_id": "ext_id"})
        self.create_motion(1, 1, motion_data={"number_value": 31})
        self.set_models(
            {
                "gender/1": {"name": "male", "organization_id": 1},
                "gender/4": {"name": "diverse", "organization_id": 1},
            }
        )

    def create_request_data(
        self, datapart: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "committee_id": 60,
            "meeting": {
                "_migration_index": MIG_INDEX,
                "meeting": {
                    "1": {
                        "id": 1,
                        "language": "en",
                        "name": "Test",
                        "description": "blablabla",
                        "admin_group_id": 1,
                        "default_group_id": 2,
                        "motions_default_amendment_workflow_id": 1,
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
                        "start_time": "1989-11-09T19:00:00+01:00",
                        "end_time": "1990-10-03T00:00:00+01:00",
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
                        "list_of_speakers_hide_contribution_count": False,
                        "list_of_speakers_enable_point_of_order_speakers": True,
                        "list_of_speakers_enable_pro_contra_speech": True,
                        "list_of_speakers_can_set_contribution_self": True,
                        "list_of_speakers_speaker_note_for_everyone": True,
                        "list_of_speakers_initially_closed": True,
                        "motions_preamble": "The assembly may decide:",
                        "motions_default_line_numbering": "none",
                        "motions_line_length": 90,
                        "motions_reason_required": False,
                        "motions_origin_motion_toggle_default": True,
                        "motions_enable_origin_motion_display": True,
                        "motions_enable_text_on_projector": True,
                        "motions_enable_reason_on_projector": True,
                        "motions_enable_sidebox_on_projector": True,
                        "motions_enable_recommendation_on_projector": True,
                        "motions_show_referring_motions": True,
                        "motions_show_sequential_number": True,
                        "motions_recommendations_by": "ABK",
                        "motions_recommendation_text_mode": "original",
                        "motions_default_sorting": "number",
                        "motions_number_type": "per_category",
                        "motions_number_min_digits": 3,
                        "motions_number_with_blank": False,
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
                        "motion_poll_default_method": "YNA",
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
                        "poll_default_live_voting_enabled": False,
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
                            "home_committee_id": 5,
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
                        "default_workflow_meeting_id": 1,
                        "state_ids": [1],
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
            "meeting_mediafile_access_group_ids": [],
            "meeting_mediafile_inherited_access_group_ids": [],
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
            "text": "<p>l&ouml;mk</p>",
            "amendment_paragraphs": {},
            "modified_final_version": "",
            "reason": "",
            "category_weight": 10000,
            "state_extension": "<p>regeer</p>",
            "recommendation_extension": None,
            "sort_weight": 10000,
            "created": "1990-07-06T00:00:00+01:00",
            "last_modified": "1990-07-22T12:00:00+01:00",
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
            "create_timestamp": "1990-07-22T12:00:00+01:00",
            "parent_id": None,
            "child_ids": [],
            "meeting_mediafile_ids": [obj_id],
            **data,
        }

    def get_meeting_mediafile_data(
        self, obj_id: int, data: dict[str, Any] = {}
    ) -> dict[str, Any]:
        return {
            "id": obj_id,
            "meeting_id": 1,
            "mediafile_id": obj_id,
            "is_public": True,
            "access_group_ids": [],
            "inherited_access_group_ids": [],
            "list_of_speakers_id": None,
            "projection_ids": [],
            "attachment_ids": [],
            **data,
        }

    def replace_migrated_projector_fields(self, data: dict[str, Any]) -> None:
        data["meeting"]["meeting"]["1"][
            "default_projector_current_list_of_speakers_ids"
        ] = data["meeting"]["meeting"]["1"].pop("default_projector_current_los_ids")
        data["meeting"]["projector"]["1"][
            "used_as_default_projector_for_current_list_of_speakers_in_meeting_id"
        ] = data["meeting"]["projector"]["1"].pop(
            "used_as_default_projector_for_current_los_in_meeting_id"
        )

    def test_no_meeting_collection(self) -> None:
        response = self.request(
            "meeting.import",
            {
                "committee_id": 1,
                "meeting": {
                    "_migration_index": MIG_INDEX,
                    "meeting": {},
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
                    "_migration_index": MIG_INDEX,
                    "meeting": {"1": {"id": 1}, "2": {"id": 2}},
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
                "committee_id": 60,
                "enable_anonymous": False,
                "is_active_in_organization_id": 1,
            },
        )
        assert start <= round(meeting_2.get("imported_at", 0).timestamp()) <= end
        user_2 = self.assert_model_exists(
            "user/2",
            {
                "username": "test",
                "meeting_ids": [2],
                "committee_ids": [60],
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
                "motion_submitter_ids": None,
                "group_ids": [4],
            },
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 2, "user_id": 1, "group_ids": [4]}
        )
        self.assert_model_exists(
            "projector/2", {"meeting_id": 2, "sequential_number": 1}
        )
        self.assert_model_exists("group/4", {"meeting_user_ids": [1, 2]})
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
            "committee/60", {"user_ids": [1, 2], "meeting_ids": [1, 2]}
        )
        self.assert_model_exists(ONE_ORGANIZATION_FQID, {"active_meeting_ids": [1, 2]})

    def test_check_calc_fields(self) -> None:
        request_data = self.create_request_data({})
        for field in ["motion_workflow_ids", "motion_state_ids"]:
            request_data["meeting"]["meeting"]["1"][field] = [1, 2, 3]
        for id_ in range(2, 4):
            request_data["meeting"]["motion_state"][str(id_)] = {
                "id": id_,
                "meeting_id": 1,
                "name": f"state{id_}",
                "weight": 1,
                "workflow_id": id_,
                "first_state_of_workflow_id": id_,
            }

        # sequential_number is given
        request_data["meeting"]["projector"]["1"]["sequential_number"] = 63
        request_data["meeting"]["motion_workflow"]["1"]["sequential_number"] = 42
        # sequential_number is smaller than max_sequential_number
        request_data["meeting"]["motion_workflow"]["2"] = {
            "id": 2,
            "meeting_id": 1,
            "name": "workflow2",
            "first_state_id": 2,
            "state_ids": [2],
            "sequential_number": 41,
        }
        # sequential_number is not given
        request_data["meeting"]["motion_workflow"]["3"] = {
            "id": 3,
            "meeting_id": 1,
            "name": "workflow3",
            "first_state_id": 3,
            "state_ids": [3],
        }

        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"meeting_ids": [2]})
        self.assert_model_exists("meeting/2", {"user_ids": [1, 2]})
        self.assert_model_exists(
            "projector/2", {"meeting_id": 2, "sequential_number": 63}
        )
        self.assert_model_exists(
            "motion_workflow/2", {"meeting_id": 2, "sequential_number": 42}
        )
        self.assert_model_exists(
            "motion_workflow/3", {"meeting_id": 2, "sequential_number": 41}
        )
        self.assert_model_exists(
            "motion_workflow/4", {"meeting_id": 2, "sequential_number": 43}
        )

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
        request_data["meeting"]["meeting"]["1"]["user_ids"] = [11]
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
                "group_ids": [4, 5],
                "committee_id": 60,
                "projector_ids": [2],
                "admin_group_id": 5,
                "default_group_id": 4,
                "motion_state_ids": [2],
                "motion_workflow_ids": [2],
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
                "group_ids": [5],
                "comment": "imported user111 for external meeting1",
            },
        )
        self.assert_model_not_exists("user/2")

        self.assert_model_exists(
            "group/1",
            {
                "meeting_id": 1,
                "name": "group1",
            },
        )
        self.assert_model_exists(
            "group/4",
            {
                "name": "imported default group2",
                "meeting_user_ids": None,
                "meeting_id": 2,
                "default_group_for_meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "group/5",
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
        request_data["meeting"]["meeting"]["1"]["user_ids"] = [1, 2]

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
            "meeting_user/1", {"meeting_id": 2, "user_id": 2, "group_ids": [4]}
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 2, "user_id": 1, "group_ids": [4]}
        )
        self.assert_model_exists(
            "group/4", {"meeting_user_ids": [1, 2], "meeting_id": 2}
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
            {"user_id": 2, "meeting_id": 2, "group_ids": [4], "personal_note_ids": [1]},
        )
        self.assert_model_exists(
            "meeting_user/2", {"user_id": 1, "meeting_id": 2, "group_ids": [4]}
        )
        self.assert_model_exists(
            "group/4",
            {
                "meeting_user_ids": [1, 2],
                "meeting_id": 2,
                "admin_group_for_meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "group/5",
            {
                "meeting_user_ids": None,
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
                "committee_ids": [60],
            },
        )

        self.assert_model_exists(
            "meeting_user/3",
            {"user_id": 2, "meeting_id": 3, "group_ids": [6], "personal_note_ids": [2]},
        )
        self.assert_model_exists(
            "meeting_user/4", {"user_id": 1, "meeting_id": 3, "group_ids": [6]}
        )
        meeting_3 = self.assert_model_exists(
            "meeting/3",
            {
                "name": "Test",
                "description": "blablabla",
                "committee_id": 60,
                "enable_anonymous": False,
                "user_ids": [1, 2],
                "group_ids": [6, 7],
                "meeting_user_ids": [3, 4],
            },
        )
        assert (
            start <= round(meeting_3.get("imported_at", 0).timestamp()) <= start + 300
        )
        self.assert_model_exists(
            "projector/3", {"meeting_id": 3, "sequential_number": 1}
        )
        self.assert_model_exists(
            "group/6",
            {
                "meeting_user_ids": [3, 4],
                "meeting_id": 3,
                "admin_group_for_meeting_id": 3,
            },
        )
        self.assert_model_exists(
            "group/7",
            {
                "name": "imported default group2",
                "meeting_user_ids": None,
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
            "committee/60", {"user_ids": [1, 2], "meeting_ids": [1, 2, 3]}
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
            "Missing OrganizationManagementLevel: superadmin"
            in response.json["message"]
        )

    def test_use_blobs(self) -> None:
        file_content = base64.b64encode(b"testtesttest").decode()
        request_data = self.create_request_data(
            {
                "mediafile": {"1": self.get_mediafile_data(1)},
                "meeting_mediafile": {"1": self.get_meeting_mediafile_data(1)},
            }
        )
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["meeting_mediafile_ids"] = [1]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        mediafile = self.assert_model_exists("mediafile/1", {"owner_id": "meeting/2"})
        assert mediafile.get("blob") is None
        self.media.upload_mediafile.assert_called_with(file_content, 1, "text/plain")
        self.assert_model_exists(
            "meeting_mediafile/1", {"mediafile_id": 1, "meeting_id": 2}
        )

    def test_inherited_access_group_ids_none(self) -> None:
        request_data = self.create_request_data(
            {
                "mediafile": {"1": self.get_mediafile_data(1)},
                "meeting_mediafile": {
                    "1": self.get_meeting_mediafile_data(
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
        request_data["meeting"]["meeting"]["1"]["meeting_mediafile_ids"] = [1]
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
                            "meeting_mediafile_access_group_ids": [1],
                            "meeting_mediafile_inherited_access_group_ids": [1],
                            "meeting_user_ids": [11],
                        },
                    ),
                    "2": self.get_group_data(
                        2,
                        {
                            "default_group_for_meeting_id": 1,
                            "meeting_mediafile_access_group_ids": [1],
                            "meeting_mediafile_inherited_access_group_ids": [1],
                        },
                    ),
                },
                "mediafile": {"1": self.get_mediafile_data(1)},
                "meeting_mediafile": {
                    "1": self.get_meeting_mediafile_data(
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
        request_data["meeting"]["meeting"]["1"]["meeting_mediafile_ids"] = [1]
        request_data["meeting"]["meeting"]["1"]["group_ids"] = [1, 2]

        # try both orders, both should work
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        # other order
        request_data["meeting"]["meeting_mediafile"]["1"][
            "inherited_access_group_ids"
        ] = [2, 1]
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
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/3",
            {
                "state_extension": "bla[motion/2]bla",
                "state_extension_reference_ids": ["motion/2"],
                "recommendation_extension": "bla[motion/2]bla",
                "recommendation_extension_reference_ids": ["motion/2"],
                "sequential_number": 2,
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
                "mediafile": {"3": self.get_mediafile_data(3)},
                "meeting_mediafile": {
                    "3": self.get_meeting_mediafile_data(
                        3,
                        {
                            "used_as_logo_web_header_in_meeting_id": 1,
                        },
                    )
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["logo_web_header_id"] = 3
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [3]
        request_data["meeting"]["meeting"]["1"]["meeting_mediafile_ids"] = [3]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/1")
        self.assert_model_exists("meeting/2", {"logo_web_header_id": 1})

    def test_font_italic_id(self) -> None:
        # Template Relation Field
        request_data = self.create_request_data(
            {
                "mediafile": {"3": self.get_mediafile_data(3)},
                "meeting_mediafile": {
                    "3": self.get_meeting_mediafile_data(
                        3,
                        {
                            "used_as_font_italic_in_meeting_id": 1,
                        },
                    )
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["font_italic_id"] = 3
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [3]
        request_data["meeting"]["meeting"]["1"]["meeting_mediafile_ids"] = [3]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/1")
        self.assert_model_exists("meeting/2", {"font_italic_id": 1})

    def test_logo_id_wrong_place(self) -> None:
        # Template Relation Field
        request_data = self.create_request_data(
            {
                "mediafile": {"3": self.get_mediafile_data(3)},
                "meeting_mediafile": {
                    "3": self.get_meeting_mediafile_data(
                        3,
                        {
                            "used_as_logo_web_in_meeting_id": 1,
                        },
                    )
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["logo_web_id"] = 3
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [3]
        request_data["meeting"]["meeting"]["1"]["meeting_mediafile_ids"] = [3]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "\tmeeting/1: Invalid fields logo_web_id (value: 3)\n\tmeeting_mediafile/3: Invalid fields used_as_logo_web_in_meeting_id (value: 1)"
            in response.json["message"]
        )

    def test_is_public_error(self) -> None:
        request_data = self.create_request_data(
            {
                "mediafile": {
                    "3": self.get_mediafile_data(
                        3,
                        {
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
                            "child_ids": [3],
                        },
                    ),
                },
                "meeting_mediafile": {
                    "3": self.get_meeting_mediafile_data(
                        3,
                        {"used_as_logo_web_header_in_meeting_id": 1},
                    ),
                    "2": self.get_meeting_mediafile_data(
                        2,
                        {
                            "is_public": False,
                        },
                    ),
                },
            }
        )
        request_data["meeting"]["meeting"]["1"]["logo_web_header_id"] = 3
        request_data["meeting"]["meeting"]["1"]["mediafile_ids"] = [2, 3]
        request_data["meeting"]["meeting"]["1"]["meeting_mediafile_ids"] = [2, 3]
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
            "meeting_user/2", {"group_ids": [4], "meeting_id": 2, "user_id": 1}
        )
        self.assert_model_exists(
            "user/2", {"meeting_user_ids": [1], "username": "test"}
        )
        self.assert_model_exists(
            "meeting_user/1", {"group_ids": [4], "meeting_id": 2, "user_id": 2}
        )
        self.assert_model_exists("meeting/2", {"user_ids": [1, 2]})
        self.assert_model_exists(
            "group/4",
            {
                "meeting_user_ids": [1, 2],
                "meeting_id": 2,
                "name": "imported admin group1",
            },
        )
        self.assert_model_exists(
            "group/5",
            {
                "name": "imported default group2",
                "meeting_user_ids": None,
                "default_group_for_meeting_id": 2,
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
                "sequential_number": 1,
            },
        )

    def test_motion_all_origin_ids(self) -> None:
        """
        This case is unrealistic, since usually you can't forward to the same meeting.
        We should test it regardless, since json-files can be edited.
        """
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
        self.assert_status_code(response, 200)
        motion = self.assert_model_exists(
            "motion/2", {"meeting_id": 2, "sequential_number": 1}
        )
        assert motion.get("all_origin_ids") is None
        motion = self.assert_model_exists(
            "motion/3", {"meeting_id": 2, "sequential_number": 2}
        )
        assert motion.get("all_derived_motion_ids") is None

    def test_foreign_motion_all_origin_ids(self) -> None:
        request_data = self.create_request_data(
            {
                "motion": {
                    "2": self.get_motion_data(
                        2,
                        {
                            "all_origin_ids": [1],
                            "list_of_speakers_id": 2,
                            "state_id": 1,
                            "origin_meeting_id": 3,
                        },
                    ),
                },
                "list_of_speakers": {
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
        request_data["meeting"]["meeting"]["1"]["motion_ids"] = [2]
        request_data["meeting"]["meeting"]["1"]["list_of_speakers_ids"] = [2]
        request_data["meeting"]["motion_state"]["1"]["motion_ids"] = [2]
        request_data["meeting"]["meeting"]["1"]["forwarded_motion_ids"] = [12, 13]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {
                "meeting_id": 2,
                "all_origin_ids": None,
                "origin_meeting_id": None,
                "sequential_number": 1,
            },
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

    def test_duplicate_external_id(self) -> None:
        request_data = self.create_request_data({})
        request_data["meeting"]["meeting"]["1"]["external_id"] = "ext_id"
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "The external id of the meeting is not unique in the organization scope. Send a differing external id with this request."
            in response.json["message"]
        )

    def test_locked_meeting(self) -> None:
        request_data = self.create_request_data({})
        request_data["meeting"]["meeting"]["1"]["locked_from_inside"] = True
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 400)
        assert "Cannot import a locked meeting." in response.json["message"]

    def test_field_check(self) -> None:
        request_data = self.create_request_data(
            {
                "mediafile": {"1": self.get_mediafile_data(1)},
                "meeting_mediafile": {
                    "1": self.get_meeting_mediafile_data(
                        1,
                        {
                            "foobar": "test this",
                        },
                    ),
                },
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
                "committee/60": {
                    "user_ids": [1, 14],
                },
                "committee/61": {
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
                        "meeting_ids": [1],
                        "organization_id": 1,
                    },
                    "13": {
                        "id": 13,
                        "username": "username_import13",
                        "email": "test_new@example.de",
                        "meeting_user_ids": [13],
                        "meeting_ids": [1],
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
        request_data["committee_id"] = 61
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["number_of_imported_users"] == 3
        assert response.json["results"][0][0]["number_of_merged_users"] == 1
        self.assert_model_exists(
            "user/1",
            {
                "username": "admin",
                "meeting_ids": [1, 2],
                "committee_ids": [60, 61],
                "meeting_user_ids": [1, 18],
            },
        )
        self.assert_model_exists(
            "user/14",
            {
                "username": "username_to_merge",
                "meeting_ids": [1, 2],
                "committee_ids": [60, 61],
                "meeting_user_ids": [14, 16],
            },
        )
        self.assert_model_exists(
            "user/15",
            {
                "username": "username_import1",
                "meeting_ids": [2],
                "committee_ids": [61],
                "meeting_user_ids": [15],
            },
        )
        self.assert_model_exists(
            "user/16",
            {
                "username": "username_import13",
                "meeting_ids": [2],
                "committee_ids": [61],
                "meeting_user_ids": [17],
            },
        )
        committee1 = self.assert_model_exists("committee/60", {"meeting_ids": [1]})
        assert sorted(committee1.get("user_ids", [])) == [1, 14]
        meeting1 = self.assert_model_exists("meeting/1", {"committee_id": 60})
        assert sorted(meeting1.get("user_ids", [])) == [1, 14]
        assert sorted(meeting1.get("meeting_user_ids", [])) == [1, 14]
        self.assert_model_exists("committee/61", {"meeting_ids": [2]})
        self.assert_model_exists("meeting/2", {"committee_id": 61})
        organization = self.assert_model_exists(
            "organization/1", {"committee_ids": [60, 61], "active_meeting_ids": [1, 2]}
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
        request_data["meeting"]["meeting"]["1"]["user_ids"] = [1, 12]
        response = self.request("meeting.import", request_data)
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["number_of_imported_users"] == 2
        assert response.json["results"][0][0]["number_of_merged_users"] == 1
        self.assert_model_exists(
            "committee/60", {"meeting_ids": [1, 2], "user_ids": [1, 14, 15]}
        )
        meeting2 = self.assert_model_exists("meeting/2", {"committee_id": 60})
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
                "user/1": {
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "vote_delegations_from_ids": [14],
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
                    "meeting_user_ids": [1, 14],
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

    @performance
    def test_big_file(self) -> None:
        data = {
            "meeting": get_initial_data_file("data/put_your_file.json"),
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
            {
                "amendment_paragraphs": {
                    "1": "&lt;it&gt;test&lt;/it&gt;",
                    "2": "broken",
                },
                "sequential_number": 1,
            },
        )

    def test_import_with_wrong_decimal(self) -> None:
        data = self.create_request_data({})
        data["meeting"]["user"]["1"]["default_vote_weight"] = "1A0"
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 400)
        assert (
            "default_vote_weight: value '1A0' couldn't be converted to decimal."
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

    def test_gender_import(self) -> None:
        """
        Each user represents different cases. The user number belongs to the request data, NOT the pre-existing-users.
        User 1 shows that a new user will be created with gender_id (also with a new gender).
        User 2 shows that a new user will be created with gender_id, but the same like User 1.
        User 3 shows that the gender is not being updated on existing user with id=2 (same name etc.).
        User 4 shows that a new user with empty gender can be created.
        User 5 shows that a new user with a second new gender will be created.
        User 6 shows that a new user will be added to an existing gender with filled user_ids.
        User 7 shows the same as User 3 but with a new gender which should not be created.
        """
        data = self.create_request_data({})
        self.update_model(ONE_ORGANIZATION_FQID, {"user_ids": [1, 2]})
        self.update_model("gender/4", {"user_ids": [2]})
        self.set_models(
            {
                "user/2": {
                    "username": "other_user",
                    "first_name": "other",
                    "last_name": "user",
                    "email": "other@us.er",
                    "organization_id": 1,
                    "gender_id": 4,
                }
            }
        )
        data["meeting"]["user"]["1"]["gender"] = "needs_to_be_created"
        other_users_request_data = {
            "2": {
                "id": 2,
                "username": "newer_user",
                "first_name": "newer",
                "last_name": "user",
                "gender": "needs_to_be_created",
                "organization_id": 1,
            },
            "3": {
                "id": 3,
                "username": "other_user",
                "first_name": "other",
                "last_name": "user",
                "email": "other@us.er",
                "gender": "male",
                "organization_id": 1,
            },
            "4": {
                "id": 4,
                "username": "new_user",
                "first_name": "new",
                "last_name": "user",
                "gender": "",
                "organization_id": 1,
            },
            "5": {
                "id": 5,
                "username": "newest_user",
                "first_name": "newest",
                "last_name": "user",
                "gender": "needs_to_be_created_too",
                "organization_id": 1,
            },
            "6": {
                "id": 6,
                "username": "ultra_newest_user",
                "first_name": "ultra newest",
                "last_name": "user",
                "gender": "diverse",
                "organization_id": 1,
            },
            "7": {
                "id": 7,
                "username": "other_user",
                "first_name": "other",
                "last_name": "user",
                "email": "other@us.er",
                "gender": "not_to_be_created",
                "organization_id": 1,
            },
        }
        data["meeting"]["user"].update(other_users_request_data)
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "other_user",
                "gender": None,
                "gender_id": 4,
            },
        )
        self.assert_model_exists(
            "user/3", {"username": "test", "gender": None, "gender_id": 5}
        )
        self.assert_model_exists(
            "user/4",
            {
                "username": "newer_user",
                "gender": None,
                "gender_id": 5,
            },
        )
        self.assert_model_exists(
            "user/5",
            {
                "username": "new_user",
                "gender": None,
                "gender_id": None,
            },
        )
        self.assert_model_exists(
            "user/6",
            {
                "username": "newest_user",
                "gender": None,
                "gender_id": 6,
            },
        )
        self.assert_model_exists(
            "user/7",
            {
                "username": "ultra_newest_user",
                "gender": None,
                "gender_id": 4,
            },
        )
        self.assert_model_exists("gender/4", {"name": "diverse", "user_ids": [2, 7]})
        self.assert_model_exists(
            "gender/5", {"name": "needs_to_be_created", "user_ids": [3, 4]}
        )
        self.assert_model_exists(
            "gender/6", {"name": "needs_to_be_created_too", "user_ids": [6]}
        )
        self.assert_model_exists(
            "organization/1",
            {"user_ids": [1, 2, 3, 4, 5, 6, 7], "gender_ids": [1, 4, 5, 6]},
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
        del meeting_data["meeting"]["1"]["user_ids"]
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

    def test_old_migration_index(self) -> None:
        """test what happens if an old migration index is sent."""
        data = self.create_request_data()
        data["meeting"]["meeting"]["1"][
            "motions_default_statute_amendment_workflow_id"
        ] = 1
        data["meeting"]["meeting"]["1"][
            "motions_statute_recommendations_by"
        ] = "Statute ABK"
        data["meeting"]["meeting"]["1"]["motions_statutes_enabled"] = True
        data["meeting"]["meeting"]["1"]["motion_statute_paragraph_ids"] = []

        data["meeting"]["motion_workflow"]["1"][
            "default_statute_amendment_workflow_meeting_id"
        ] = 1
        data["meeting"]["_migration_index"] = 55
        self.replace_migrated_projector_fields(data)
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 400)
        assert (
            "Your data migration index '55' is lower than the migration index of this backend"
            in response.json["message"]
        )
        assert "Please, use a more recent file!" in response.json["message"]

    @pytest.mark.skip()
    def test_import_os3_data(self) -> None:
        data_raw = get_initial_data_file("data/export-OS3-demo.json")
        data = {"committee_id": 1, "meeting": data_raw}
        response = self.request("meeting.import", data)
        self.assert_status_code(response, 200)

    def test_import_export_with_orga_mediafiles(self) -> None:
        self.create_meeting()
        self.set_user_groups(1, [1])
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
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
                    "name": "Test",
                    "description": "blablabla",
                    "motions_default_amendment_workflow_id": 1,
                    "reference_projector_id": 1,
                    "projector_countdown_default_time": 60,
                    "projector_countdown_warning_time": 5,
                    "projector_ids": [1],
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
                    "logo_projector_main_id": 20,
                    "list_of_speakers_ids": [1, 9, 11, 12],
                    "all_projection_ids": [2, 8],
                    "motion_ids": [3],
                    "topic_ids": [4],
                    "assignment_ids": [5],
                    "speaker_ids": [6],
                    "structure_level_list_of_speakers_ids": [7],
                    "agenda_item_ids": [10],
                    "point_of_order_category_ids": [13],
                    "structure_level_ids": [14],
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
                "meeting_user/1": {"speaker_ids": [6]},
                "motion_workflow/1": {
                    "name": "blup",
                    "default_amendment_workflow_meeting_id": 1,
                    "sequential_number": 1,
                },
                "motion_state/1": {
                    "css_class": "lightblue",
                    "workflow_id": 1,
                    "name": "test",
                    "weight": 1,
                    "restrictions": [],
                    "allow_support": False,
                    "allow_create_poll": False,
                    "allow_submitter_edit": False,
                    "set_number": True,
                    "show_state_extension_field": False,
                    "merge_amendment_into_final": "undefined",
                    "show_recommendation_extension_field": False,
                    "motion_ids": [3],
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
                    "current_projection_ids": [8],
                    "history_projection_ids": [2],
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
                    "list_of_speakers_id": 1,
                    "projection_ids": [2],
                    "attachment_ids": ["motion/3", "topic/4", "assignment/5"],
                    "used_as_logo_projector_main_in_meeting_id": 1,
                },
                "list_of_speakers/2": {
                    "sequential_number": 2,
                    "content_object_id": "meeting_mediafile/20",
                    "speaker_ids": [6],
                    "structure_level_list_of_speakers_ids": [7],
                    "projection_ids": [8],
                    "meeting_id": 1,
                },
                "list_of_speakers/9": {
                    "sequential_number": 3,
                    "content_object_id": "motion/3",
                    "meeting_id": 1,
                },
                "list_of_speakers/11": {
                    "sequential_number": 4,
                    "content_object_id": "topic/4",
                    "meeting_id": 1,
                },
                "list_of_speakers/12": {
                    "sequential_number": 5,
                    "content_object_id": "assignment/5",
                    "meeting_id": 1,
                },
                "projection/2": {
                    "content_object_id": "meeting_mediafile/20",
                    "history_projector_id": 1,
                    "meeting_id": 1,
                },
                "projection/8": {
                    "content_object_id": "list_of_speakers/1",
                    "current_projector_id": 1,
                    "meeting_id": 1,
                },
                "motion/3": {
                    "sequential_number": 2,
                    "title": "A motion",
                    "text": "like no other",
                    "state_id": 1,
                    "list_of_speakers_id": 9,
                    "attachment_meeting_mediafile_ids": [20],
                    "meeting_id": 1,
                },
                "topic/4": {
                    "title": "Stupid topic",
                    "sequential_number": 1,
                    "attachment_meeting_mediafile_ids": [20],
                    "agenda_item_id": 10,
                    "list_of_speakers_id": 11,
                    "meeting_id": 1,
                },
                "assignment/5": {
                    "title": "We're electing someone, idk",
                    "sequential_number": 1,
                    "list_of_speakers_id": 12,
                    "attachment_meeting_mediafile_ids": [20],
                    "meeting_id": 1,
                },
                "speaker/6": {
                    "list_of_speakers_id": 2,
                    "structure_level_list_of_speakers_id": 7,
                    "meeting_user_id": 1,
                    "point_of_order": True,
                    "point_of_order_category_id": 13,
                    "meeting_id": 1,
                },
                "structure_level_list_of_speakers/7": {
                    "structure_level_id": 14,
                    "list_of_speakers_id": 1,
                    "speaker_ids": [6],
                    "initial_time": 100,
                    "remaining_time": 5,
                    "meeting_id": 1,
                },
                "agenda_item/10": {"content_object_id": "topic/4", "meeting_id": 1},
                "point_of_order_category/13": {
                    "text": "Pointless point of order",
                    "rank": 1,
                    "meeting_id": 1,
                    "speaker_ids": [6],
                },
                "structure_level/14": {
                    "name": "Eeeeueuuurrrggghhhh",
                    "structure_level_list_of_speakers_ids": [7],
                    "meeting_id": 1,
                },
                "mediafile/3": {
                    "title": "Child_of_mother_of_all_directories.pdf",
                    "filename": "COMOAD.pdf",
                    "filesize": 750000,
                    "mimetype": "application/pdf",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "parent_id": 1,
                    "pdf_information": Jsonb({"pages": 1}),
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
        presenterapp = create_presenter_test_application()
        presenterclient = Client(presenterapp, self.update_vote_service_auth_data)
        presenterclient.login("admin", "admin", 1)
        self.auth_data = deepcopy(presenterclient.auth_data)
        response = presenterclient.post(
            get_route_path(PresenterView.presenter_route),
            json=[{"presenter": "export_meeting", "data": {"meeting_id": 1}}],
        )
        status_code, export = (response.status_code, response.json[0])
        assert status_code == 200
        self.auth_data = deepcopy(self.client.auth_data)
        self.set_models(
            {"meeting/1": {"external_id": "NewExternalIdToStopReimportDetection"}}
        )
        import_response = self.request(
            "meeting.import", {"committee_id": 60, "meeting": export}
        )
        self.assert_status_code(import_response, 200)
        self.assert_model_exists(
            "meeting/2",
            {
                "committee_id": 60,
                "group_ids": [4, 5, 6],
                "projector_ids": [2],
                "meeting_mediafile_ids": [],
                "logo_projector_main_id": None,
                "list_of_speakers_ids": [13, 14, 15],
                "all_projection_ids": [],
                "motion_ids": [4],
                "topic_ids": [5],
                "assignment_ids": [6],
                "speaker_ids": [],
                "structure_level_list_of_speakers_ids": [],
                "agenda_item_ids": [11],
                "point_of_order_category_ids": [14],
                "structure_level_ids": [15],
            },
        )
        for id_ in [4, 5]:
            self.assert_model_exists(
                f"group/{id_}",
                {
                    "meeting_id": 2,
                    "meeting_mediafile_access_group_ids": [],
                    "meeting_mediafile_inherited_access_group_ids": [],
                },
            )
        self.assert_model_exists(
            "group/6",
            {
                "meeting_mediafile_access_group_ids": [],
                "meeting_mediafile_inherited_access_group_ids": None,
                "meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "meeting_user/2", {"user_id": 1, "meeting_id": 2, "speaker_ids": []}
        )
        self.assert_model_exists(
            "projector/2",
            {
                "meeting_id": 2,
                "current_projection_ids": [],
                "history_projection_ids": [],
            },
        )
        self.assert_model_not_exists("mediafile/6")
        self.assert_model_not_exists("meeting_mediafile/51")
        for id_ in range(1, 6):
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "meeting_mediafile_ids": [id_ * 10],
                },
            )
        for id_, co_id in {13: "motion/4", 14: "topic/5", 15: "assignment/6"}.items():
            self.assert_model_exists(
                f"list_of_speakers/{id_}",
                {
                    "sequential_number": id_ - 11,
                    "meeting_id": 2,
                    "content_object_id": co_id,
                },
            )
        self.assert_model_not_exists("projection/9")
        self.assert_model_exists(
            "motion/4",
            {
                "sequential_number": 1,
                "title": "A motion",
                "text": "like no other",
                "state_id": 2,
                "list_of_speakers_id": 13,
                "attachment_meeting_mediafile_ids": [],
                "meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "topic/5",
            {
                "title": "Stupid topic",
                "sequential_number": 1,
                "attachment_meeting_mediafile_ids": [],
                "agenda_item_id": 11,
                "list_of_speakers_id": 14,
                "meeting_id": 2,
            },
        )
        self.assert_model_exists(
            "assignment/6",
            {
                "title": "We're electing someone, idk",
                "sequential_number": 1,
                "list_of_speakers_id": 15,
                "attachment_meeting_mediafile_ids": [],
                "meeting_id": 2,
            },
        )
        self.assert_model_not_exists("speaker/7")
        self.assert_model_exists(
            "agenda_item/11", {"content_object_id": "topic/5", "meeting_id": 2}
        )
        self.assert_model_exists(
            "point_of_order_category/14",
            {
                "text": "Pointless point of order",
                "rank": 1,
                "meeting_id": 2,
                "speaker_ids": [],
            },
        )
        self.assert_model_exists(
            "structure_level/15",
            {
                "name": "Eeeeueuuurrrggghhhh",
                "meeting_id": 2,
                "structure_level_list_of_speakers_ids": [],
            },
        )
