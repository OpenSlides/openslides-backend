from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestGetUSerEditable(BasePresenterTestCase):
    def test_good(self) -> None:
        self.create_model(
            "user/111",
            {
                "username": "Helmhut",
                "last_name": "Schmidt",
                "is_active": True,
                "password": self.auth.hash("Kohl"),
                "default_password": "Kohl",
                "committee_management_ids": [2]
            }
        )
        self.login(111)
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
            }
        )
        status_code, data = self.request(
            "get_user_editable", {"user_ids": [2, 3, 4, 5, 6, 7]}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            {
                "2": {
                    "editable": False,
                    "message": 'Your organization management level is not high enough to change a user with a Level of can_manage_users!'
                },
                "3": {
                    "editable": True,
                },
                "4": {
                    "editable": True,
                },
                "5": {
                    "editable": True,
                },
                "6": {
                    "editable": False,
                    "message": 'Your organization management level is not high enough to change a user with a Level of superadmin!'
                },
                "7": {
                    "editable": True,
                },
            },
        )

    def test_without_user_None(self) -> None:
        status_code, data = self.request("get_user_editable", {"user_ids": [None]})
        self.assertEqual(status_code, 400)
        self.assertIn("data.user_ids[0] must be integer", data["message"])

    def test_without_user_empty_list(self) -> None:
        status_code, data = self.request("get_user_editable", {"user_ids": []})
        self.assertEqual(status_code, 200)
        assert data == {}
