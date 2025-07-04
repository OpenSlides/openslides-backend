from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestGetUSerScope(BasePresenterTestCase):
    def test_good(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "committee_id": 2,
                    "is_active_in_organization_id": 1,
                },
                # archived meeting
                "meeting/2": {
                    "committee_id": 2,
                    "is_active_in_organization_id": None,
                    "is_archived_in_organization_id": 1,
                },
                "committee/1": {},
                "committee/2": {"meeting_ids": [1, 2]},
                "user/2": {
                    "username": "only_oml_level",
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                },
                "user/3": {
                    "username": "only_cml_level",
                    "committee_management_ids": [1],
                    "meeting_ids": [],
                },
                "user/4": {
                    "username": "cml_and_meeting",
                    "meeting_ids": [1],
                    "committee_management_ids": [2],
                },
                "user/5": {
                    "username": "no_organization",
                    "meeting_ids": [],
                },
                "user/6": {
                    "username": "oml_and_meeting",
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                    "meeting_ids": [1],
                },
                "user/7": {
                    "username": "meeting_and_archived_meeting",
                    "meeting_ids": [1, 2],
                },
                "user/8": {
                    "username": "with_home_committee",
                    "home_committee_id": 2,
                },
                "user/9": {
                    "username": "with_home_committee_and_meeting",
                    "home_committee_id": 1,
                    "meeting_ids": [1, 2],
                },
            }
        )
        status_code, data = self.request(
            "get_user_scope", {"user_ids": [2, 3, 4, 5, 6, 7, 8, 9]}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            {
                "2": {
                    "collection": "organization",
                    "id": 1,
                    "user_oml": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "committee_ids": [],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": None,
                },
                "3": {
                    "collection": "committee",
                    "id": 1,
                    "user_oml": "",
                    "committee_ids": [1],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": None,
                },
                "4": {
                    "collection": "meeting",
                    "id": 1,
                    "user_oml": "",
                    "committee_ids": [2],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": None,
                },
                "5": {
                    "collection": "organization",
                    "id": 1,
                    "user_oml": "",
                    "committee_ids": [],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": None,
                },
                "6": {
                    "collection": "meeting",
                    "id": 1,
                    "user_oml": OrganizationManagementLevel.SUPERADMIN,
                    "committee_ids": [2],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": None,
                },
                "7": {
                    "collection": "meeting",
                    "id": 1,
                    "user_oml": "",
                    "committee_ids": [2],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": None,
                },
                "8": {
                    "collection": "committee",
                    "id": 2,
                    "user_oml": "",
                    "committee_ids": [],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": 2,
                },
                "9": {
                    "collection": "committee",
                    "id": 1,
                    "user_oml": "",
                    "committee_ids": [2],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": 1,
                },
            },
        )

    def test_without_user_None(self) -> None:
        status_code, data = self.request("get_user_scope", {"user_ids": [None]})
        self.assertEqual(status_code, 400)
        self.assertIn("data.user_ids[0] must be integer", data["message"])

    def test_without_user_empty_list(self) -> None:
        status_code, data = self.request("get_user_scope", {"user_ids": []})
        self.assertEqual(status_code, 200)
        assert data == {}
