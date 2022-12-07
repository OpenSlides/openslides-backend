from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class OrganizationDeleteHistoryInformation(BaseActionTestCase):
    def test_delete_history_information_no_permission(self) -> None:
        self.set_models(
            {
                "organization/1": {"name": "Orga"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                },
            }
        )
        response = self.request("organization.delete_history_information", {"id": 1})
        self.assert_status_code(response, 403)

    def test_delete_history_information_correct(self) -> None:
        self.set_models(
            {
                "organization/1": {"name": "Orga", "enable_electronic_voting": True},
                "meeting/1": {"name": "Meeting", "is_active_in_organization_id": 1},
                "assignment/1": {
                    "title": "test_assignment_ohneivoh9caiB8Yiungo",
                    "open_posts": 1,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "content_object_id": "assignment/1",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", ["Ballot created"])

        response = self.request("organization.delete_history_information", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", None)
