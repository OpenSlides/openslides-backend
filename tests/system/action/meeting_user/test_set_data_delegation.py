from typing import Any

from tests.system.action.base import BaseActionTestCase
from tests.util import Response


class UserUpdateDelegationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "committee/1": {"meeting_ids": [222]},
                "meeting/222": {
                    "name": "Meeting222",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "meeting_user_ids": [11, 12, 13, 14],
                    "default_group_id": 11,
                },
                "meeting/223": {
                    "name": "Meeting223",
                    "is_active_in_organization_id": 1,
                    "default_group_id": 12,
                },
                "group/1": {"meeting_id": 222, "meeting_user_ids": [11, 12, 13, 14]},
                "group/2": {"meeting_id": 223, "meeting_user_ids": [21]},
                "group/11": {"meeting_id": 222, "default_group_for_meeting_id": 222},
                "group/12": {"meeting_id": 223, "default_group_for_meeting_id": 223},
                "user/1": {"meeting_user_ids": [11, 21], "meeting_ids": [222]},
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
                    "username": "delegator2",
                    "meeting_ids": [222],
                    "meeting_user_ids": [14],
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
                "meeting_user/14": {
                    "meeting_id": 222,
                    "user_id": 4,
                    "group_ids": [1],
                },
                "meeting_user/21": {
                    "meeting_id": 223,
                    "user_id": 1,
                    "group_ids": [2],
                },
            }
        )

    def request_executor(self, meeting_user4_update: dict[str, Any]) -> Response:
        request_data: dict[str, Any] = {
            "id": 14,
        }
        request_data.update(meeting_user4_update)
        return self.request("meeting_user.set_data", request_data)

    def test_delegated_to_standard_user(self) -> None:
        response = self.request_executor({"vote_delegated_to_id": 13})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_id": 13})
        self.assert_model_exists(
            "meeting_user/13", {"vote_delegations_from_ids": [12, 14]}
        )

    def test_delegated_to_error_self(self) -> None:
        response = self.request_executor({"vote_delegated_to_id": 14})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 4 can't delegate the vote to himself.", response.json["message"]
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
        response = self.request_executor({"vote_delegated_to_id": 21})
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

    def test_delegated_to_error_user_cannot_delegate_has_delegations_himself(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting_user/14": {"vote_delegations_from_ids": [12]},
                "meeting_user/12": {"vote_delegated_to_id": 14},
            }
        )
        response = self.request_executor({"vote_delegated_to_id": 11})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 4 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )

    def test_reverse_delegation(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting_user/14": {"vote_delegations_from_ids": [13]},
                "meeting_user/13": {
                    "vote_delegated_to_id": 14,
                    "vote_delegations_from_ids": [],
                },
            }
        )
        response = self.request_executor(
            {"vote_delegations_from_ids": [], "vote_delegated_to_id": 13}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/14",
            {"vote_delegated_to_id": 13, "vote_delegations_from_ids": []},
        )
        self.assert_model_exists(
            "meeting_user/13",
            {"vote_delegated_to_id": None, "vote_delegations_from_ids": [14]},
        )
        # also test the reverse direction of reversing the delegation direction
        response = self.request_executor(
            {"vote_delegations_from_ids": [13], "vote_delegated_to_id": None}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/14",
            {"vote_delegated_to_id": None, "vote_delegations_from_ids": [13]},
        )
        self.assert_model_exists(
            "meeting_user/13",
            {"vote_delegated_to_id": 14, "vote_delegations_from_ids": []},
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
        response = self.request_executor(
            {"vote_delegations_from_ids": [12], "group_ids": [2]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 222: ['group/2']",
            response.json["message"],
        )

    def test_delegations_from_error_target_meeting_dont_match(self) -> None:
        response = self.request_executor({"vote_delegations_from_ids": [21]})
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

    def test_delegations_from_error_self(self) -> None:
        response = self.request_executor({"vote_delegations_from_ids": [14]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 4 can't delegate the vote to himself.", response.json["message"]
        )

    def test_reset_vote_delegated_to_ok(self) -> None:
        self.set_models(
            {
                "meeting_user/14": {"vote_delegated_to_id": 13},
                "meeting_user/13": {"vote_delegations_from_ids": [12, 14]},
            }
        )
        response = self.request_executor({"vote_delegated_to_id": None})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_id": None})
        self.assert_model_exists("meeting_user/13", {"vote_delegations_from_ids": [12]})

    def test_reset_vote_delegations_from_ok(self) -> None:
        self.set_models(
            {
                "meeting_user/14": {"vote_delegations_from_ids": [12, 13]},
                "meeting_user/12": {"vote_delegated_to_id": 14},
                "meeting_user/13": {"vote_delegated_to_id": 14},
            }
        )
        response = self.request_executor({"vote_delegations_from_ids": [12]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegations_from_ids": [12]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_id": 14})
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_id": None})

    def test_delegations_from_on_empty_array_standard_user(self) -> None:
        self.set_models(
            {
                "meeting_user/14": {"vote_delegations_from_ids": [12, 13]},
                "meeting_user/12": {"vote_delegated_to_id": 14},
                "meeting_user/13": {"vote_delegated_to_id": 14},
            }
        )
        response = self.request_executor({"vote_delegations_from_ids": []})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegations_from_ids": []})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_id": None})
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_id": None})

    def test_delegated_to_error_user_cant_delegate_to_user_who_delegated(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"vote_delegations_from_ids": [13]},
                "meeting_user/13": {"vote_delegated_to_id": 12},
            }
        )
        response = self.request_executor({"vote_delegated_to_id": 13})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 4 cannot delegate his vote to user 3, because that user has delegated his vote himself.",
            response.json["message"],
        )

    def test_delegated_replace_existing_to_other_user(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_id": 13},
                "meeting_user/13": {"vote_delegations_from_ids": [12, 14]},
                "meeting_user/14": {"vote_delegated_to_id": 13},
            }
        )
        response = self.request_executor({"vote_delegated_to_id": 11})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegations_from_ids": [14]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_id": 13})
        self.assert_model_exists("meeting_user/13", {"vote_delegations_from_ids": [12]})
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_id": 11})

    def test_replace_existing_delegations_from_1(self) -> None:
        self.set_models(
            {
                "meeting_user/11": {"vote_delegated_to_id": 14},
                "meeting_user/12": {"vote_delegated_to_id": 13},
                "meeting_user/13": {"vote_delegations_from_ids": [12]},
                "meeting_user/14": {"vote_delegations_from_ids": [11]},
            }
        )
        response = self.request_executor({"vote_delegations_from_ids": [11, 12]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegated_to_id": 14})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_id": 14})
        self.assert_model_exists("meeting_user/13", {"vote_delegations_from_ids": []})
        self.assert_model_exists(
            "meeting_user/14", {"vote_delegations_from_ids": [11, 12]}
        )

    def test_vote_add_1_remove_other_2_from_standard_user(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting_user/11": {"vote_delegated_to_id": 14},
                "meeting_user/12": {"vote_delegated_to_id": 14},
                "meeting_user/13": {"vote_delegations_from_ids": []},
                "meeting_user/14": {"vote_delegations_from_ids": [11, 12]},
            }
        )

        response = self.request_executor({"vote_delegations_from_ids": [13]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegated_to_id": None})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_id": None})
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_id": 14})
        self.assert_model_exists("meeting_user/14", {"vote_delegations_from_ids": [13]})

    def test_delegations_from_but_delegated_own(self) -> None:
        self.set_models(
            {
                "meeting_user/13": {"vote_delegations_from_ids": [12, 14]},
                "meeting_user/14": {"vote_delegated_to_id": 13},
            }
        )
        response = self.request_executor({"vote_delegations_from_ids": [11]})

        self.assert_status_code(response, 400)
        self.assertIn(
            "User 4 cannot receive vote delegations, because he delegated his own vote.",
            response.json["message"],
        )

    def test_delegations_from_target_user_receives_delegations(self) -> None:
        response = self.request_executor({"vote_delegations_from_ids": [13]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User(s) [3] can't delegate their votes because they receive vote delegations.",
            response.json["message"],
        )

    def test_vote_setting_both_correct_from_to_1_standard_user(self) -> None:
        """meeting_user2/4 -> meeting_user3: meeting_user4 reset own delegation and receives other delegation"""
        self.set_models(
            {
                "meeting_user/14": {"vote_delegated_to_id": 13},
                "meeting_user/13": {"vote_delegations_from_ids": [12, 14]},
            }
        )

        response = self.request_executor(
            {"vote_delegations_from_ids": [11], "vote_delegated_to_id": None}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegated_to_id": 14})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_id": 13})
        self.assert_model_exists("meeting_user/13", {"vote_delegations_from_ids": [12]})
        self.assert_model_exists("meeting_user/14", {"vote_delegations_from_ids": [11]})

    def test_vote_setting_both_correct_from_to_2_standard_user(self) -> None:
        """meeting_user2/3 -> meeting_user4: meeting_user4 delegates to meeting_user/1 and resets it's received delegations"""
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_id": 14},
                "meeting_user/13": {
                    "vote_delegated_to_id": 14,
                    "vote_delegations_from_ids": [],
                },
                "meeting_user/14": {"vote_delegations_from_ids": [12, 13]},
            }
        )

        response = self.request_executor(
            {"vote_delegations_from_ids": [], "vote_delegated_to_id": 11}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegations_from_ids": [14]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_id": None})
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_id": None})
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_id": 11})

    def test_vote_setting_both_from_to_error_standard_user_1(self) -> None:
        """meeting_user2/3 -> meeting_user4: meeting_user4 delegates to meeting_user/13 and resets received delegation from meeting_user/13"""
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_id": 14},
                "meeting_user/13": {
                    "vote_delegated_to_id": 14,
                    "vote_delegations_from_ids": [],
                },
                "meeting_user/14": {"vote_delegations_from_ids": [12, 13]},
            }
        )
        response = self.request_executor(
            {"vote_delegations_from_ids": [12], "vote_delegated_to_id": 13}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 4 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )

    def test_vote_add_remove_delegations_from_standard_user_ok(self) -> None:
        """user2/3 -> user4: user4 removes 2 and adds 1 delegations_from"""
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_id": 14},
                "meeting_user/13": {
                    "vote_delegated_to_id": 14,
                    "vote_delegations_from_ids": [],
                },
                "meeting_user/14": {"vote_delegations_from_ids": [12, 13]},
            }
        )
        response = self.request_executor({"vote_delegations_from_ids": [13, 11]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegated_to_id": 14})
        self.assert_model_exists(
            "meeting_user/14", {"vote_delegations_from_ids": [13, 11]}
        )
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_id": 14})
