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
                    "meeting_user_ids": [2, 3, 4],
                },
                "group/1": {"meeting_id": 222, "meeting_user_ids": [2, 3, 4]},
                "user/1": {"meeting_ids": [222]},
                "user/2": {
                    "username": "user/2",
                    "meeting_user_ids": [2],
                    "meeting_ids": [222],
                },
                "user/3": {
                    "username": "user3",
                    "meeting_user_ids": [3],
                    "meeting_ids": [222],
                },
                "user/4": {
                    "username": "user4",
                    "meeting_user_ids": [4],
                    "meeting_ids": [222],
                },
                "meeting_user/2": {
                    "meeting_id": 222,
                    "user_id": 2,
                    "vote_delegated_to_id": 3,
                    "group_ids": [1],
                },
                "meeting_user/3": {
                    "meeting_id": 222,
                    "user_id": 3,
                    "vote_delegations_from_ids": [2],
                    "group_ids": [1],
                },
                "meeting_user/4": {
                    "meeting_id": 222,
                    "user_id": 4,
                    "group_ids": [1],
                },
            }
        )

    def request_executor(
        self, action: str, meeting_user4_update: Dict[str, Any]
    ) -> Response:
        request_data: Dict[str, Any] = {"user_id": 4, "meeting_id": 222}
        request_data.update(meeting_user4_update)
        return self.request(action, request_data)

    def test_create_delegated_to_error_standard_user(self) -> None:
        response = self.request_executor(
            "meeting_user.create", {"vote_delegated_to_id": 2}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "MeetingUser 5 cannot delegate his vote to user 2, because that user has delegated his vote himself.",
            response.json["message"],
        )

    def test_create_delegated_to_standard_user(self) -> None:
        response = self.request_executor(
            "meeting_user.create", {"vote_delegated_to_id": 3}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/5", {"vote_delegated_to_id": 3})
        self.assert_model_exists(
            "meeting_user/3", {"vote_delegations_from_ids": [2, 5]}
        )

    def test_create_delegations_from_user2_standard_user(self) -> None:
        response = self.request_executor(
            "meeting_user.create", {"vote_delegations_from_ids": [2]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/5", {"vote_delegations_from_ids": [2]})
        self.assert_model_exists("meeting_user/2", {"vote_delegated_to_id": 5})

    def test_create_delegations_from_user3_error_standard_user(self) -> None:
        response = self.request_executor(
            "meeting_user.create", {"vote_delegations_from_ids": [3]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "MeetingUser(s) [3] can't delegate their votes because they receive vote delegations.",
            response.json["message"],
        )
