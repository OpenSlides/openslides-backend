from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestGetUSerScope(BasePresenterTestCase):
    def test_good(self) -> None:
        self.create_meeting()
        self.create_meeting(
            4,
            meeting_data={
                "committee_id": 60,
                "is_active_in_organization_id": None,
                "is_archived_in_organization_id": 1,
            },
        )
        self.set_models(
            {
                "user/2": {
                    "username": "only_oml_level",
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                },
                "user/3": {"username": "only_cml_level"},
                "user/4": {"username": "cml_and_meeting"},
                "user/5": {"username": "no_organization"},
                "user/6": {
                    "username": "oml_and_meeting",
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                },
                "user/7": {"username": "meeting_and_archived_meeting"},
                "user/8": {
                    "username": "with_home_committee",
                    "home_committee_id": 60,
                },
                "user/9": {
                    "username": "with_home_committee_and_meeting",
                    "home_committee_id": 63,
                },
                "committee/60": {"manager_ids": [4]},
                "committee/63": {"manager_ids": [3]},
                "meeting_user/14": {"meeting_id": 1, "user_id": 4},
                "meeting_user/16": {"meeting_id": 1, "user_id": 6},
                "meeting_user/17": {"meeting_id": 1, "user_id": 7},
                "meeting_user/47": {"meeting_id": 4, "user_id": 7},
                "meeting_user/19": {"meeting_id": 1, "user_id": 9},
                "meeting_user/49": {"meeting_id": 4, "user_id": 9},
                "group/1": {"meeting_user_ids": [14, 16, 17, 19]},
                "group/4": {"meeting_user_ids": [47, 49]},
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
                    "id": 63,
                    "user_oml": "",
                    "committee_ids": [63],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": None,
                },
                "4": {
                    "collection": "meeting",
                    "id": 1,
                    "user_oml": "",
                    "committee_ids": [60],
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
                    "committee_ids": [60],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": None,
                },
                "7": {
                    "collection": "meeting",
                    "id": 1,
                    "user_oml": "",
                    "committee_ids": [60],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": None,
                },
                "8": {
                    "collection": "committee",
                    "id": 60,
                    "user_oml": "",
                    "committee_ids": [],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": 60,
                },
                "9": {
                    "collection": "committee",
                    "id": 63,
                    "user_oml": "",
                    "committee_ids": [60],
                    "user_in_archived_meetings_only": False,
                    "home_committee_id": 63,
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
