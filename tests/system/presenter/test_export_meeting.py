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
        assert data["meeting"]["1"]["organization_tag_ids"] is None

    def test_add_users(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "exported_meeting",
                    "user_ids": [1],
                    "group_ids": [11],
                    "present_user_ids": [1],
                },
                "user/1": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [11],
                    "comment_$": ["1"],
                    "comment_$1": "blablabla",
                    "number_$": ["1"],
                    "number_$1": "spamspamspam",
                    "is_present_in_meeting_ids": [1],
                },
                "group/11": {
                    "name": "group_in_meeting_1",
                    "meeting_id": 1,
                    "user_ids": [1],
                },
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        assert status_code == 200
        assert data["user"]["1"]["organization_management_level"] == "superadmin"
        assert data["user"]["1"]["username"] == "admin"
        assert data["user"]["1"]["is_active"] is True
        assert data["user"]["1"]["group_$_ids"] == ["1"]
        assert data["user"]["1"]["group_$1_ids"] == [11]
        assert data["user"]["1"]["meeting_ids"] == [1]
        assert data["user"]["1"]["is_present_in_meeting_ids"] == [1]
        assert data["user"]["1"]["comment_$"] == ["1"]
        assert data["user"]["1"]["comment_$1"] == "blablabla"
        assert data["user"]["1"]["number_$"] == ["1"]
        assert data["user"]["1"]["number_$1"] == "spamspamspam"
