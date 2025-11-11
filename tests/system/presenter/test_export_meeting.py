from datetime import datetime

from openslides_backend.action.action_worker import ActionWorkerState
from openslides_backend.models.models import Poll
from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestExportMeeting(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1, {"name": "exported_meeting"})

    def test_correct(self) -> None:
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        assert data["meeting"]["1"]["name"] == "exported_meeting"
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
            "option",
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
        self.set_models(
            {
                "meeting/1": {"present_user_ids": [1]},
                "gender/1": {"name": "male"},
                "user/1": {"gender_id": 1},
            }
        )
        self.set_user_groups(1, [1])
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200

        user = data["user"]["1"]
        assert user["organization_management_level"] == "superadmin"
        assert user["username"] == "admin"
        assert user["is_active"] is True
        assert user["is_present_in_meeting_ids"] == [1]
        assert user["gender"] == "male"

        assert data["meeting_user"]["1"]["group_ids"] == [1]

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

        meeting_user_2 = data["meeting_user"]["2"]
        assert meeting_user_2.get("meeting_id") == 1
        assert meeting_user_2.get("user_id") == 12
        assert meeting_user_2.get("personal_note_ids") == [34]

    def test_export_meeting_find_special_users(self) -> None:
        """Find users in:
        Collection | Field
        meeting    | present_user_ids
        motion     | supporter_meeting_user_ids
        poll       | voted_ids
        vote       | delegated_meeting_user_id
        """
        self.create_motion(1, 30)
        self.set_models(
            {
                "meeting/1": {"present_user_ids": [11]},
                "group/1": {"meeting_user_ids": [112, 114]},
                "user/11": {"username": "exuser11"},
                "user/12": {"username": "exuser12"},
                "user/13": {"username": "exuser13"},
                "user/14": {"username": "exuser14"},
                "meeting_user/112": {
                    "meeting_id": 1,
                    "user_id": 12,
                    "supported_motion_ids": [30],
                },
                "meeting_user/114": {
                    "meeting_id": 1,
                    "user_id": 14,
                },
                "poll/80": {
                    "title": "Poll 80",
                    "type": Poll.TYPE_NAMED,
                    "backend": "fast",
                    "pollmethod": "YNA",
                    "onehundred_percent_base": "YNA",
                    "meeting_id": 1,
                    "content_object_id": "motion/30",
                    "state": Poll.STATE_PUBLISHED,
                    "voted_ids": [13],
                },
                "vote/120": {
                    "meeting_id": 1,
                    "delegated_user_id": 14,
                    "user_id": 14,
                    "user_token": "asdfgh",
                    "option_id": 1,
                },
                "option/1": {"meeting_id": 1},
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["meeting"]["1"].get("user_ids") is None
        for id_ in ("11", "12", "13", "14"):
            assert data["user"][id_]
