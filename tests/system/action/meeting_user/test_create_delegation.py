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
                    "meeting_user_ids": [11, 12, 13],
                },
                "group/1": {"meeting_id": 222, "meeting_user_ids": [11, 12, 13]},
                "user/1": {"meeting_user_ids": [11], "meeting_ids": [222]},
                "user/2": {
                    "username": "user/2",
                    "meeting_user_ids": [12],
                    "meeting_ids": [222],
                },
                "user/3": {
                    "username": "user3",
                    "meeting_user_ids": [13],
                    "meeting_ids": [222],
                },
                "user/4": {
                    "username": "user4",
                },
                "meeting_user/11": {
                    "meeting_id": 222,
                    "user_id": 1,
                    "group_ids": [1],
                },
                "meeting_user/12": {
                    "meeting_id": 222,
                    "user_id": 2,
                    "vote_delegated_to_id": 13,
                    "group_ids": [1],
                },
                "meeting_user/13": {
                    "meeting_id": 222,
                    "user_id": 3,
                    "vote_delegations_from_ids": [12],
                    "group_ids": [1],
                },
            }
        )

    def request_executor(self, meeting_user4_update: Dict[str, Any]) -> Response:
        request_data: Dict[str, Any] = {
            "user_id": 4,
            "meeting_id": 222,
            "group_ids": [1],
        }
        request_data.update(meeting_user4_update)
        return self.request("meeting_user.create", request_data)

    def test_delegated_to_standard_user(self) -> None:
        response = self.request_executor({"vote_delegated_to_id": 13})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_id": 13})
        self.assert_model_exists(
            "meeting_user/13", {"vote_delegations_from_ids": [12, 14]}
        )

    def test_delegated_to_success_without_group(self) -> None:
        response = self.request_executor({"group_ids": [], "vote_delegated_to_id": 13})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/14",
            {
                "vote_delegated_to_id": 13,
                "group_ids": [],
                "meeting_id": 222,
                "user_id": 4,
            },
        )
        self.assert_model_exists(
            "meeting_user/13", {"vote_delegations_from_ids": [12, 14]}
        )

    def test_delegated_to_error_group_do_not_match_meeting(self) -> None:
        self.set_models(
            {
                "meeting/223": {
                    "name": "Meeting223",
                    "is_active_in_organization_id": 1,
                },
                "group/2": {"meeting_id": 223},
            }
        )
        response = self.request_executor({"vote_delegated_to_id": 13, "group_ids": [2]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 222: ['group/2']",
            response.json["message"],
        )

    def test_delegated_to_error_wrong_target_meeting(self) -> None:
        self.set_models(
            {
                "meeting/223": {
                    "name": "Meeting223",
                    "is_active_in_organization_id": 1,
                },
                "group/2": {"meeting_id": 223, "meeting_user_ids": [10]},
                "user/1": {
                    "meeting_user_ids": [11, 10],
                    "meeting_ids": [222, 223],
                },
                "meeting_user/10": {
                    "user_id": 1,
                    "meeting_id": 223,
                    "group_ids": [2],
                },
            },
        )
        response = self.request_executor({"vote_delegated_to_id": 10})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1's delegation id don't belong to meeting 222.",
            response.json["message"],
        )

    def test_delegated_to_error_target_user_delegated_himself(self) -> None:
        response = self.request_executor({"vote_delegated_to_id": 12})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 4 cannot delegate his vote to user 2, because that user has delegated his vote himself.",
            response.json["message"],
        )

    def test_delegated_to_error_target_not_exists(self) -> None:
        response = self.request_executor({"vote_delegated_to_id": 1000})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model 'meeting_user/1000' does not exist.",
            response.json["message"],
        )

    def test_delegations_from_ok(self) -> None:
        response = self.request_executor({"vote_delegations_from_ids": [12]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegations_from_ids": [12]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_id": 14})

    def test_delegations_from_error_group_do_not_match_meeting(self) -> None:
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
            {"vote_delegations_from_ids": [12], "group_ids": [2]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 222: ['group/2']",
            response.json["message"],
        )

    def test_delegations_from_error_target_meeting_dont_match(self) -> None:
        self.set_models(
            {
                "meeting/223": {
                    "name": "Meeting223",
                    "is_active_in_organization_id": 1,
                },
                "group/2": {"meeting_id": 223, "meeting_user_ids": [11]},
                "user/1": {
                    "meeting_user_ids": [11],
                    "meeting_ids": [223],
                },
                "meeting_user/11": {
                    "meeting_id": 223,
                    "user_id": 1,
                    "group_ids": [2],
                },
            }
        )
        response = self.request_executor(
            {"vote_delegations_from_ids": [11], "group_ids": [1]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User(s) [1] delegation ids don't belong to meeting 222.",
            response.json["message"],
        )

    def test_delegations_from_error_target_user_receives_delegations(self) -> None:
        response = self.request_executor({"vote_delegations_from_ids": [13]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User(s) [3] can't delegate their votes because they receive vote delegations.",
            response.json["message"],
        )

    def test_delegations_from_target_not_exists(self) -> None:
        response = self.request_executor({"vote_delegations_from_ids": [1000]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model 'meeting_user/1000' does not exist.",
            response.json["message"],
        )
