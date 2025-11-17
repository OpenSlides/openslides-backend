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
        self.create_user(
            "only_oml_level",
            organization_management_level=OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
        only_cml_level = self.create_user("only_cml_level")
        self.set_committee_management_level([63], only_cml_level)
        cml_and_meeting = self.create_user(
            "cml_and_meeting",
            group_ids=[1],
        )
        self.set_committee_management_level([60], cml_and_meeting)
        self.create_user("no_organization")
        self.create_user(
            "oml_and_meeting",
            organization_management_level=OrganizationManagementLevel.SUPERADMIN,
            group_ids=[1],
        )
        self.create_user(
            "meeting_and_archived_meeting",
            group_ids=[1, 4],
        )
        self.create_user(
            "with_home_committee",
            home_committee_id=60,
        )
        self.create_user(
            "with_home_committee_and_meetings",
            group_ids=[1, 4],
            home_committee_id=63,
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
