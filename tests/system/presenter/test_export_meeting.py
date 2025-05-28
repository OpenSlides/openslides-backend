from time import time

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.permissions.management_levels import OrganizationManagementLevel

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
                    "supporter_meeting_user_ids": [112],
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
                    "supported_motion_ids": [30],
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
