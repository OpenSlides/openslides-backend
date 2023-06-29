from os import environ
from typing import Callable, Optional

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import ACTION_URL
from tests.system.base import ADMIN_PASSWORD, ADMIN_USERNAME
from tests.system.util import create_action_test_application
from tests.util import AuthData, Client

from .base import BasePresenterTestCase


class TestGetActiveUsersAmount(BasePresenterTestCase):
    def get_action_application(self) -> WSGIApplication:
        return create_action_test_application()

    def create_action_client(
        self, on_auth_data_changed: Optional[Callable[[AuthData], None]] = None
    ) -> Client:
        return Client(self.app_action, on_auth_data_changed)

    def setUp(self) -> None:
        super().setUp()
        self.app_action = self.get_action_application()
        self.client_action = self.create_action_client(
            self.update_vote_service_auth_data
        )
        if self.auth_data:
            # Reuse old login data to avoid a new login request
            self.client_action.update_auth_data(self.auth_data)
        else:
            # Login and save copy of auth data for all following tests
            self.client_action.login(ADMIN_USERNAME, ADMIN_PASSWORD)

    def setup_data_with_archived_and_deleted_meetings(self):
        """The set models are basically taken from meeting/test_archive.py/test_archive_with_users
        and from meeting/test_delete.py to have the correct data set depending the implementation
        of the actions
        """
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "committee_ids": [1],
                    "active_meeting_ids": [1, 2, 3, 4],
                    "archived_meeting_ids": [],
                    "user_ids": [1, 2, 3, 4, 5, 6, 7],
                },
                "committee/1": {
                    "name": "test_committee",
                    "organization_id": 1,
                    "meeting_ids": [1, 2, 3, 4],
                    "default_meeting_id": 1,
                    "user_ids": [1, 2, 3, 4, 5, 6, 7],
                    "user_$_management_level": ["can_manage"],
                    "user_$can_manage_management_level": [3, 5],
                },
                "meeting/1": {
                    "name": "to archive",
                    "user_ids": [2, 4, 5],
                    "group_ids": [1],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "default_meeting_for_committee_id": 1,
                },
                "meeting/2": {
                    "name": "active",
                    "user_ids": [4],
                    "group_ids": [2],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "meeting/3": {
                    "name": "to delete",
                    "user_ids": [6],
                    "group_ids": [3],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "meeting/4": {
                    "name": "to archive and delete",
                    "user_ids": [7],
                    "group_ids": [4],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "group/1": {"user_ids": [2, 4, 5], "meeting_id": 1, "name": "g1"},
                "group/2": {"user_ids": [4], "meeting_id": 2, "name": "g2"},
                "group/3": {"user_ids": [6], "meeting_id": 3, "name": "g3"},
                "group/4": {"user_ids": [7], "meeting_id": 4, "name": "g4"},
                "user/2": {
                    "username": "in archived meeting",
                    "meeting_ids": [1],
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
                "user/3": {
                    "username": "only committee manager",
                    "meeting_ids": [],
                    "committee_$_management_level": ["can_manage"],
                    "committee_$can_manage_management_level": [1],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
                "user/4": {
                    "username": "in active and archived meeting",
                    "meeting_ids": [1, 2],
                    "group_$_ids": ["1", "2"],
                    "group_$1_ids": [1],
                    "group_$2_ids": [2],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
                "user/5": {
                    "username": "in archived meeting and committee",
                    "meeting_ids": [1],
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "committee_$_management_level": ["can_manage"],
                    "committee_$can_manage_management_level": [1],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
                "user/6": {
                    "username": "in deleted meeting",
                    "meeting_ids": [3],
                    "group_$_ids": ["3"],
                    "group_$3_ids": [3],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
                "user/7": {
                    "username": "in meeting archived and deleted",
                    "meeting_ids": [4],
                    "group_$_ids": ["4"],
                    "group_$4_ids": [4],
                    "committee_ids": [1],
                    "organization_id": 1,
                    "is_active": True,
                },
            }
        )

        response = self.client_action.post(
            ACTION_URL,
            json=[{"action": "meeting.archive", "data": [{"id": 1}]}],
            headers={},
        )
        self.assert_status_code(response, 200)
        response = self.client_action.post(
            ACTION_URL,
            json=[{"action": "meeting.delete", "data": [{"id": 3}]}],
            headers={},
        )
        self.assert_status_code(response, 200)
        response = self.client_action.post(
            ACTION_URL,
            json=[{"action": "meeting.archive", "data": [{"id": 4}]}],
            headers={},
        )
        self.assert_status_code(response, 200)
        response = self.client_action.post(
            ACTION_URL,
            json=[{"action": "meeting.delete", "data": [{"id": 4}]}],
            headers={},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("organization/1", {
            "active_meeting_ids": [2],
            "archived_meeting_ids": [1],
            "user_ids": [1, 2, 3, 4, 5, 6, 7],
        })
        self.assert_model_exists("committee/1", {
            "meeting_ids": [1, 2],
            "user_ids": [1, 2, 3, 4, 5],
            "user_$_management_level": ["can_manage"],
            "user_$can_manage_management_level": [3, 5],
        })

    def test_correct_standard_mode(self) -> None:
        environ["USER_COUNT_MODE"] = "standard"
        self.set_models(
            {
                "user/1": {"is_active": True},
                "user/2": {"is_active": True},
                "user/3": {"is_active": False},
                "user/4": {"is_active": True},
                "user/5": {"is_active": False},
            }
        )
        status_code, data = self.request("get_active_users_amount", {})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"active_users_amount": 3})

    def test_correct_no_archived_meetings_mode(self) -> None:
        environ["USER_COUNT_MODE"] = "no_archived_meetings"
        self.set_models(
            {
                "user/1": {"is_active": True},
                "user/2": {"is_active": True},
                "user/3": {"is_active": False},
                "user/4": {"is_active": True},
                "user/5": {"is_active": False},
            }
        )
        status_code, data = self.request("get_active_users_amount", {})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"active_users_amount": 0})

    def test_with_archived_and_deleted_meetings_standard_mode(self) -> None:
        environ["USER_COUNT_MODE"] = "standard"
        self.setup_data_with_archived_and_deleted_meetings()
        status_code, data = self.request("get_active_users_amount", {})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"active_users_amount": 7})

    def test_with_archived_and_deleted_meetings_no_archived_meetings_mode(self) -> None:
        environ["USER_COUNT_MODE"] = "no_archived_meetings"
        self.setup_data_with_archived_and_deleted_meetings()
        status_code, data = self.request("get_active_users_amount", {})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"active_users_amount": 1})

    def test_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                }
            }
        )
        status_code, data = self.request("get_active_users_amount", {})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"active_users_amount": 1})

    def test_no_permissions(self) -> None:
        self.set_models({"user/1": {"organization_management_level": None}})
        status_code, data = self.request("get_active_users_amount", {})
        self.assertEqual(status_code, 403)

