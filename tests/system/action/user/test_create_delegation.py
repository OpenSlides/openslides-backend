from typing import Any, Dict

from tests.system.action.base import BaseActionTestCase
from tests.util import Response


class UserCreateDelegationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "committee/1": {"meeting_ids": [222]},
                "meeting/222": {
                    "name": "Meeting222",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "group/1": {"meeting_id": 222, "user_ids": [2, 3]},
                "user/1": {"meeting_ids": [222]},
                "user/2": {
                    "username": "user/2",
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                    "vote_delegated_$222_to_id": 3,
                    "vote_delegated_$_to_id": ["222"],
                    "meeting_ids": [222],
                },
                "user/3": {
                    "username": "user3",
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                    "vote_delegations_$222_from_ids": [2],
                    "vote_delegations_$_from_ids": ["222"],
                    "meeting_ids": [222],
                },
            }
        )

    def request_executor(self, action: str, user4_update: Dict[str, Any]) -> Response:
        request_data: Dict[str, Any] = {"username": "user/4"}
        request_data["group_$_ids"] = {"222": [1]}
        request_data.update(user4_update)
        return self.request(action, request_data)

    def test_create_delegated_to_error_standard_user(self) -> None:
        response = self.request_executor(
            "user.create", {"vote_delegated_$_to_id": {222: 2}}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 4 cannot delegate his vote to user 2, because that user has delegated his vote himself.",
            response.json["message"],
        )

    def test_create_delegated_to_standard_user(self) -> None:
        response = self.request_executor(
            "user.create", {"vote_delegated_$_to_id": {222: 3}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/4", {"vote_delegated_$222_to_id": 3})
        self.assert_model_exists("user/3", {"vote_delegations_$222_from_ids": [2, 4]})

    def test_create_delegated_to_error_meeting_1_standard_user(self) -> None:
        self.set_models(
            {
                "meeting/223": {
                    "name": "Meeting223",
                    "is_active_in_organization_id": 1,
                },
                "group/2": {"meeting_id": 223},
            }
        )
        response = self.request_executor(
            "user.create",
            {"vote_delegated_$_to_id": {"222": 2}, "group_$_ids": {"223": [2]}},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 222: ['user/4']",
            response.json["message"],
        )

    def test_create_delegated_to_error_meeting_2_standard_user(self) -> None:
        self.set_models(
            {
                "meeting/223": {
                    "name": "Meeting223",
                    "is_active_in_organization_id": 1,
                },
                "group/2": {"meeting_id": 223, "user_ids": [1]},
                "user/1": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                    "meeting_ids": [223],
                },
            }
        )
        response = self.request_executor(
            "user.create",
            {"vote_delegated_$_to_id": {"223": 1}, "group_$_ids": {"222": [1]}},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 223: ['user/4']",
            response.json["message"],
        )

    def test_create_delegations_from_user2_standard_user(self) -> None:
        response = self.request_executor(
            "user.create", {"vote_delegations_$_from_ids": {222: [2]}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/4", {"vote_delegations_$222_from_ids": [2]})
        self.assert_model_exists("user/2", {"vote_delegated_$222_to_id": 4})

    def test_create_delegations_from_user3_error_standard_user(self) -> None:
        response = self.request_executor(
            "user.create", {"vote_delegations_$_from_ids": {222: [3]}}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User(s) [3] can't delegate their votes because they receive vote delegations.",
            response.json["message"],
        )

    def test_create_delegations_from_error_meeting_1_standard_user(self) -> None:
        self.set_models(
            {
                "meeting/223": {
                    "name": "Meeting223",
                    "is_active_in_organization_id": 1,
                },
                "group/2": {"meeting_id": 223},
            }
        )
        response = self.request_executor(
            "user.create",
            {"vote_delegations_$_from_ids": {"222": [2]}, "group_$_ids": {"223": [2]}},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 222: ['user/4']",
            response.json["message"],
        )

    def test_create_delegations_from_error_meeting_2_standard_user(self) -> None:
        self.set_models(
            {
                "meeting/223": {
                    "name": "Meeting223",
                    "is_active_in_organization_id": 1,
                },
                "group/2": {"meeting_id": 223, "user_ids": [1]},
                "user/1": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                    "meeting_ids": [223],
                },
            }
        )
        response = self.request_executor(
            "user.create",
            {"vote_delegations_$_from_ids": {"223": [1]}, "group_$_ids": {"222": [1]}},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 223: ['user/4']",
            response.json["message"],
        )
