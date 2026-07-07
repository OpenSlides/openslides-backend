from datetime import datetime
from zoneinfo import ZoneInfo

from openslides_backend.models.models import Poll
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class OrganizationDeleteHistoryInformation(BaseActionTestCase):
    def test_delete_history_information_no_permission(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request("organization.delete_history_information", {"id": 1})
        self.assert_status_code(response, 403)

    def test_delete_history_information_correct(self) -> None:
        self.create_meeting()
        self.create_user_for_meeting(1)
        self.set_models(
            {
                "organization/1": {"name": "Orga", "enable_electronic_voting": True},
                "assignment/1": {
                    "title": "test_assignment_ohneivoh9caiB8Yiungo",
                    "open_posts": 1,
                    "meeting_id": 1,
                },
                "list_of_speakers/1": {
                    "content_object_id": "assignment/1",
                    "meeting_id": 1,
                },
                "poll/1": {
                    "title": "test",
                    "meeting_id": 1,
                    "content_object_id": "assignment/1",
                    "visibility": Poll.VISIBILITY_MANUALLY,
                    "state": Poll.STATE_FINISHED,
                    "config_id": "poll_config_rating_approval/1",
                    "result": '{"yes": "3", "no": "2", "abstain": "1"}',
                },
                "poll_config_rating_approval/1": {
                    "poll_id": 1,
                    "onehundred_percent_base": Poll.ONEHUNDRED_PERCENT_BASE_VALID,
                    "allow_abstain": True,
                },
                "poll_option/1": {"poll_id": 1, "text": "Delete this item?"},
                "history_position/1": {
                    "timestamp": datetime.fromtimestamp(1761760881, ZoneInfo("UTC")),
                    "original_user_id": 1,
                    "user_id": 1,
                },
                "history_entry/1": {
                    "position_id": 1,
                    "meeting_id": 1,
                    "entries": ["Ballot created"],
                    "original_model_id": "assignment/1",
                    "model_id": "assignment/1",
                },
            }
        )

        response = self.request("organization.delete_history_information", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", None)
        for collection in ["history_position", "history_entry"]:
            self.assert_model_not_exists(f"{collection}/1")
