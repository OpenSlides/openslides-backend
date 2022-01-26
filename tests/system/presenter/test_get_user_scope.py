from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)

from .base import BasePresenterTestCase


class TestGetUSerScope(BasePresenterTestCase):
    def test_good(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "meeting1",
                    "committee_id": 2,
                    "is_active_in_organization_id": 1,
                },
                "committee/1": {},
                "committee/2": {"meeting_ids": [1]},
                "user/2": {
                    "username": "florian",
                    "first_name": "Florian",
                    "last_name": "Freiheit",
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                },
                "user/3": {
                    "username": "goofi",
                    "first_name": "Testy",
                    "last_name": "Tester",
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "committee_$can_manage_management_level": [1],
                    "meeting_ids": [],
                },
                "user/4": {
                    "username": "john",
                    "first_name": "John",
                    "last_name": "Xylon",
                    "meeting_ids": [1],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "committee_$can_manage_management_level": [2],
                },
            }
        )
        status_code, data = self.request("get_user_scope", {"user_ids": [2, 3, 4]})
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            {
                "2": {"collection": "organization", "id": 1},
                "3": {"collection": "committee", "id": 1},
                "4": {"collection": "meeting", "id": 1},
            },
        )
