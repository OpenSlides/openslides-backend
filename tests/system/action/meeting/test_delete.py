import pytest
from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


@pytest.mark.skip(reason="Waiting for PR from Hannes.")
class MeetingDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_delete_no_permissions(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 403)
        self.assertEqual(
            "Missing permission: CommitteeManagementLevel can_manage in committee 60",
            response.json["message"],
        )

    def test_delete_permissions_can_manage_organization(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")

    def test_delete_permissions_can_manage_committee(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        self.set_committee_management_level([60])
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")

    @pytest.mark.skip(
        reason="Requires example-data.json. TODO: unskip once it is added."
    )
    def test_delete_full_meeting(self) -> None:
        self.load_example_data()
        self.set_models(
            {
                "projection/5": {
                    "current_projector_id": None,
                    "preview_projector_id": None,
                    "history_projector_id": 1,
                    "content_object_id": "meeting/1",
                    "stable": False,
                    "type": None,
                    "weight": 1,
                    "options": {},
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")
        self.assert_model_exists("committee/1", {"meeting_ids": []})
        # assert all related models are deleted
        for i in range(5):
            self.assert_model_not_exists(f"group/{i+1}")
        self.assert_model_not_exists("personal_note/1")
        for i in range(3):
            self.assert_model_not_exists(f"tag/{i+1}")
        for i in range(15):
            self.assert_model_not_exists(f"agenda_item/{i+1}")
        for i in range(16):
            self.assert_model_not_exists(f"list_of_speakers/{i+1}")
        for i in range(13):
            self.assert_model_not_exists(f"speaker/{i+1}")
        for i in range(8):
            self.assert_model_not_exists(f"topic/{i+1}")
        for i in range(4):
            self.assert_model_not_exists(f"motion/{i+1}")
        for i in range(4):
            self.assert_model_not_exists(f"motion_submitter/{i+1}")
        self.assert_model_not_exists("motion_comment/1")
        self.assert_model_not_exists("motion_comment_section/1")
        for i in range(2):
            self.assert_model_not_exists(f"motion_category/{i+1}")
        self.assert_model_not_exists("motion_block/1")
        for i in range(2):
            self.assert_model_not_exists(f"motion_change_recommendation/{i+4}")
        for i in range(14):
            self.assert_model_not_exists(f"motion_state/{i+1}")
        for i in range(2):
            self.assert_model_not_exists(f"motion_workflow/{i+1}")
        for i in range(5):
            self.assert_model_not_exists(f"poll/{i+1}")
        for i in range(13):
            self.assert_model_not_exists(f"option/{i+1}")
        for i in range(9):
            self.assert_model_not_exists(f"vote/{i+1}")
        for i in range(2):
            self.assert_model_not_exists(f"assignment/{i+1}")
        for i in range(5):
            self.assert_model_not_exists(f"assignment_candidate/{i+1}")
        for i in range(1):
            self.assert_model_not_exists(f"mediafile/{i+1}")
        for i in range(1):
            self.assert_model_not_exists(f"meeting_mediafile/{i+1}")
        for i in range(2):
            self.assert_model_not_exists(f"projector/{i+1}")
        for i in range(5):
            self.assert_model_not_exists(f"projection/{i+1}")
        self.assert_model_not_exists("projector_message/1")
        for i in range(2):
            self.assert_model_not_exists(f"projector_countdown/{i+1}")
        for i in range(2):
            self.assert_model_not_exists(f"chat_group/{i+1}")

    def test_delete_with_tag_and_motion(self) -> None:
        self.set_models(
            {
                "tag/42": {"name": "A really special tag", "meeting_id": 1},
                "motion/1": {"meeting_id": 1, "tag_ids": [42]},
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/60", {"meeting_ids": None})
        self.assert_model_not_exists("meeting/1")
        self.assert_model_not_exists("tag/42")
        self.assert_model_not_exists("motion/1")

    def test_delete_with_history_projection(self) -> None:
        self.set_models(
            {
                "projection/42": {
                    "meeting_id": 1,
                    "content_object_id": "meeting/1",
                    "history_projector_id": 1,
                    "current_projector_id": 1,
                    "stable": False,
                },
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/60", {"meeting_ids": None})
        self.assert_model_not_exists("meeting/1")
        self.assert_model_not_exists("projector/1")
        self.assert_model_not_exists("projection/42")

    def test_delete_meeting_with_relations(self) -> None:
        user1 = self.create_user("user")
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, user1
        )
        self.set_committee_management_level([60], user1)

        self.create_user_for_meeting(1)
        everything = self.datastore.get_everything()

        # self.set_models(
        #     {
        #         "committee/1": {
        #             "user_ids": [1, 2],
        #             "manager_ids": [1],
        #         },
        #         "user/1": {
        #             "committee_management_ids": [1],
        #             "organization_management_level": "can_manage_users",
        #             "committee_ids": [1],
        #         },
        #         "user/2": {
        #             "committee_ids": [1],
        #             "meeting_user_ids": [2],
        #         },
        #         "meeting_user/2": {
        #             "meeting_id": 1,
        #             "user_id": 2,
        #             "group_ids": [11],
        #         },
        #         "group/11": {
        #             "meeting_user_ids": [2],
        #         },
        #         "meeting/1": {
        #             "user_ids": [2],
        #             "meeting_user_ids": [2],
        #         },
        #     }
        # )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")

        self.assert_model_exists(
            ONE_ORGANIZATION_FQID, {"active_meeting_ids": None, "committee_ids": [1]}
        )
        self.assert_model_exists(
            "committee/1",
            {"user_ids": [1], "meeting_ids": None, "manager_ids": [1]},
        )
        self.assert_model_not_exists("group/11")
        self.assert_model_exists(
            "user/1",
            {"committee_ids": [1], "committee_management_ids": [1]},
        )
        self.assert_model_exists(
            "user/2", {"meeting_user_ids": None, "committee_ids": None}
        )
        self.assert_model_not_exists("meeting_user/2")

    def test_delete_archived_meeting(self) -> None:
        self.set_models({"meeting/1": {"is_active_in_organization_id": None}})
        user1 = self.create_user("user")
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, user1
        )
        self.set_committee_management_level([60], user1)
        self.create_user_for_meeting(1)

        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")

    def test_delete_with_poll_candidates_and_speakers(self) -> None:
        data: dict[str, dict[str, Any]] = {
            "meeting/100": {
                "committee_id": 1,
                "meeting_user_ids": [110, 111, 112],
                "group_ids": [120],
                "assignment_ids": [140],
                "poll_ids": [150],
                "option_ids": [160],
                "poll_candidate_list_ids": [170],
                "poll_candidate_ids": [180, 181],
                "list_of_speakers_ids": [190],
                "speaker_ids": [210, 211, 212],
            },
            "meeting_user/110": {
                "meeting_id": 100,
                "user_id": 220,
                "group_ids": [120],
                "speaker_ids": [210],
            },
            "meeting_user/111": {
                "meeting_id": 100,
                "user_id": 221,
                "group_ids": [120],
                "speaker_ids": [211],
            },
            "meeting_user/112": {
                "meeting_id": 100,
                "user_id": 222,
                "group_ids": [120],
                "speaker_ids": [212],
            },
            "group/120": {"meeting_id": 100, "meeting_user_ids": [110, 111, 112]},
            "assignment/140": {"meeting_id": 100, "poll_ids": [150]},
            "poll/150": {
                "meeting_id": 100,
                "content_object_id": "assignment/140",
                "option_ids": [160],
            },
            "option/160": {
                "meeting_id": 100,
                "poll_id": 150,
                "content_object_id": "poll_candidate_list/170",
            },
            "poll_candidate_list/170": {
                "meeting_id": 100,
                "option_id": 160,
                "poll_candidate_ids": [180, 181],
            },
            "poll_candidate/180": {
                "meeting_id": 100,
                "poll_candidate_list_id": 170,
                "user_id": 220,
            },
            "poll_candidate/181": {
                "meeting_id": 100,
                "poll_candidate_list_id": 170,
                "user_id": 221,
            },
            "list_of_speakers/190": {
                "meeting_id": 100,
                "content_object_id": "assignment/140",
                "speaker_ids": [210, 211, 212],
            },
            "speaker/210": {
                "meeting_id": 100,
                "list_of_speakers_id": 190,
                "meeting_user_id": 110,
                "begin_time": 1234567,
                "end_time": 1234578,
            },
            "speaker/211": {
                "meeting_id": 100,
                "list_of_speakers_id": 190,
                "meeting_user_id": 111,
                "begin_time": 1234589,
            },
            "speaker/212": {
                "meeting_id": 100,
                "list_of_speakers_id": 190,
                "meeting_user_id": 112,
            },
        }
        self.set_models(
            {
                **data,
                ONE_ORGANIZATION_FQID: {"active_meeting_ids": [101]},
                "committee/1": {
                    "user_ids": [1, 220, 221, 222],
                    "manager_ids": [1],
                },
                "user/220": {"meeting_user_ids": [110], "poll_candidate_ids": [180]},
                "user/221": {"meeting_user_ids": [111], "poll_candidate_ids": [181]},
                "user/222": {"meeting_user_ids": [112]},
            }
        )
        response = self.request("meeting.delete", {"id": 100})
        self.assert_status_code(response, 200)
        for fqid in data:
            self.assert_model_not_exists(fqid)
        for i in range(220, 222):
            self.assert_model_exists(f"user/{i}", {})

    def test_delete_with_locked_meeting(self) -> None:
        self.base_permission_test(
            {},
            "meeting.delete",
            {"id": 1},
            OrganizationManagementLevel.SUPERADMIN,
            False,
            lock_meeting=True,
        )
        self.assert_model_not_exists("meeting/1")

    def test_delete_permissions_oml_locked_meeting_not_allowed(
        self,
    ) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual("Cannot delete locked meeting.", response.json["message"])

    def test_delete_permissions_committee_admin_locked_meeting_not_allowed(
        self,
    ) -> None:
        self.set_organization_management_level(None)
        self.set_committee_management_level([60])
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertEqual("Cannot delete locked meeting.", response.json["message"])

    def test_delete_permissions_committee_admin_locked_meeting_with_oml(
        self,
    ) -> None:
        self.set_committee_management_level([60])
        self.set_models({"meeting/1": {"locked_from_inside": True}})
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")

    def test_delete_permissions_oml_locked_meeting_with_can_manage_settings(
        self,
    ) -> None:
        self.base_permission_test(
            {},
            "meeting.delete",
            {"id": 1},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            False,
            lock_meeting=True,
        )
        self.assert_model_not_exists("meeting/1")

    def test_delete_with_public_orga_file(self) -> None:
        self.create_mediafile()
        self.set_models(
            {
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": True,
                },
            }
        )
        response = self.request("meeting.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting/1")
        self.assert_model_not_exists("meeting_mediafile/2")
        self.assert_model_exists("mediafile/1", {"meeting_mediafile_ids": None})
