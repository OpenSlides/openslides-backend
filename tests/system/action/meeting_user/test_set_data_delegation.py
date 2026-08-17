from typing import Any

from tests.system.action.base import BaseActionTestCase
from tests.util import Response


class UserUpdateDelegationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)
        self.create_meeting(225)
        self.set_models(
            {
                "group/224": {"meeting_user_ids": [11, 12, 13, 14]},
                "group/227": {"meeting_user_ids": [21]},
                "user/2": {"username": "user2"},
                "user/3": {"username": "user3"},
                "user/4": {"username": "delegator2"},
                "meeting_user/11": {"meeting_id": 222, "user_id": 1},
                "meeting_user/12": {
                    "meeting_id": 222,
                    "user_id": 2,
                    "vote_delegated_to_ids": [13],
                },
                "meeting_user/13": {"meeting_id": 222, "user_id": 3},
                "meeting_user/14": {"meeting_id": 222, "user_id": 4},
                "meeting_user/21": {"meeting_id": 225, "user_id": 1},
            }
        )

    def request_executor(self, meeting_user4_update: dict[str, Any]) -> Response:
        request_data: dict[str, Any] = {
            "id": 14,
        }
        request_data.update(meeting_user4_update)
        return self.request("meeting_user.set_data", request_data)

    def test_delegated_to_standard_user(self) -> None:
        response = self.request_executor({"vote_delegated_to_ids": [13]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_ids": [13]})
        self.assert_model_exists(
            "meeting_user/13", {"vote_delegations_from_ids": [12, 14]}
        )

    def test_delegated_to_multiple_users(self) -> None:
        self.set_models({"meeting/222": {"users_vote_delegations_max_amount": 2}})
        response = self.request_executor({"vote_delegated_to_ids": [11, 13]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_ids": [11, 13]})
        self.assert_model_exists("meeting_user/11", {"vote_delegations_from_ids": [14]})
        self.assert_model_exists(
            "meeting_user/13", {"vote_delegations_from_ids": [12, 14]}
        )

    def test_delegated_to_error_self(self) -> None:
        response = self.request_executor({"vote_delegated_to_ids": [14]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 4 can't delegate the vote to himself.", response.json["message"]
        )

    def test_delegated_to_without_group(self) -> None:
        response = self.request_executor(
            {"group_ids": [], "vote_delegated_to_ids": [13]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Update of meeting_user/14: You try to set following required fields to an empty value: ['group_ids']",
            response.json["message"],
        )

    def test_delegated_to_error_group_do_not_match_meeting(self) -> None:
        response = self.request_executor(
            {"vote_delegated_to_ids": [13], "group_ids": [227]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 225: ['meeting_user/14']",
            response.json["message"],
        )

    def test_delegated_to_error_wrong_target_meeting(self) -> None:
        self.set_models({"meeting/222": {"users_vote_delegations_max_amount": 2}})
        response = self.request_executor({"vote_delegated_to_ids": [13, 21]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User(s) [1] delegation ids don't belong to meeting 222.",
            response.json["message"],
        )

    def test_delegated_to_error_wrong_target_meeting_multi(self) -> None:
        self.set_models(
            {
                "meeting/222": {"users_vote_delegations_max_amount": 3},
                "group/227": {"meeting_user_ids": [21, 22]},
                "user/5": {"username": "user5"},
                "meeting_user/22": {"meeting_id": 225, "user_id": 5},
            }
        )
        response = self.request_executor({"vote_delegated_to_ids": [13, 21, 22]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User(s) [1, 5] delegation ids don't belong to meeting 222.",
            response.json["message"],
        )

    def test_delegated_to_error_target_user_delegated_himself(self) -> None:
        response = self.request_executor({"vote_delegated_to_ids": [12]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User 4 cannot delegate his vote to user(s) [2], because these users have delegated their votes themselves.",
            response.json["message"],
        )

    def test_delegated_to_error_target_user_delegated_himself_multi(self) -> None:
        self.set_models(
            {
                "meeting/222": {"users_vote_delegations_max_amount": 2},
                "group/224": {"meeting_user_ids": [11, 12, 13, 14, 15]},
                "user/5": {"username": "user5"},
                "meeting_user/15": {
                    "meeting_id": 222,
                    "user_id": 5,
                    "vote_delegated_to_ids": [11],
                },
            }
        )
        response = self.request_executor({"vote_delegated_to_ids": [12, 15]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User 4 cannot delegate his vote to user(s) [2, 5], because these users have delegated their votes themselves.",
            response.json["message"],
        )

    def test_delegated_to_error_target_user_delegates_to_self_and_other_user(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting/222": {"users_vote_delegations_max_amount": 2},
                "meeting_user/12": {"vote_delegated_to_ids": [14, 13]},
            }
        )
        response = self.request_executor(
            {"vote_delegations_from_ids": [], "vote_delegated_to_ids": [12]}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User 4 cannot delegate his vote to user(s) [2], because these users have delegated their votes themselves.",
            response.json["message"],
        )

    def test_delegated_to_error_user_cannot_delegate_has_delegations_himself(
        self,
    ) -> None:
        self.set_models({"meeting_user/12": {"vote_delegated_to_ids": [14]}})
        response = self.request_executor({"vote_delegated_to_ids": [11]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User 4 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )

    def test_reverse_delegation(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_ids": None},
                "meeting_user/13": {"vote_delegated_to_ids": [14]},
            }
        )
        response = self.request_executor(
            {"vote_delegations_from_ids": [], "vote_delegated_to_ids": [13]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/14",
            {"vote_delegated_to_ids": [13], "vote_delegations_from_ids": None},
        )
        self.assert_model_exists(
            "meeting_user/13",
            {"vote_delegated_to_ids": None, "vote_delegations_from_ids": [14]},
        )
        # also test the reverse direction of reversing the delegation direction
        response = self.request_executor(
            {"vote_delegations_from_ids": [13], "vote_delegated_to_ids": []}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/14",
            {"vote_delegated_to_ids": None, "vote_delegations_from_ids": [13]},
        )
        self.assert_model_exists(
            "meeting_user/13",
            {"vote_delegated_to_ids": [14], "vote_delegations_from_ids": None},
        )

    def test_delegated_to_error_target_not_exists(self) -> None:
        response = self.request_executor({"vote_delegated_to_ids": [1000]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model 'meeting_user/1000' does not exist.",
            response.json["message"],
        )

    def test_delegations_from_add_ok(self) -> None:
        self.set_models({"meeting/222": {"users_vote_delegations_max_amount": 2}})
        response = self.request_executor({"vote_delegations_from_ids": [12]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegations_from_ids": [12]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_ids": [13, 14]})
        self.assert_model_exists("meeting_user/13", {"vote_delegations_from_ids": [12]})

    def test_delegations_from_error_group_do_not_match_meeting(self) -> None:
        self.set_models({"meeting/222": {"users_vote_delegations_max_amount": 2}})
        response = self.request_executor(
            {"vote_delegations_from_ids": [12], "group_ids": [227]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 225: ['meeting_user/14']",
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
                "meeting_user/14": {"vote_delegated_to_ids": [13]},
            }
        )
        response = self.request_executor({"vote_delegated_to_ids": []})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_ids": None})
        self.assert_model_exists("meeting_user/13", {"vote_delegations_from_ids": [12]})

    def test_reset_vote_delegations_from_ok(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_ids": [14]},
                "meeting_user/13": {"vote_delegated_to_ids": [14]},
            }
        )
        response = self.request_executor({"vote_delegations_from_ids": [12]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegations_from_ids": [12]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_ids": [14]})
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_ids": None})

    def test_delegations_from_on_empty_array_standard_user(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_ids": [14]},
                "meeting_user/13": {"vote_delegated_to_ids": [14]},
            }
        )
        response = self.request_executor({"vote_delegations_from_ids": []})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/14", {"vote_delegations_from_ids": None})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_ids": None})
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_ids": None})

    def test_delegated_to_error_user_cant_delegate_to_user_who_delegated(self) -> None:
        self.set_models(
            {
                "meeting_user/13": {"vote_delegated_to_ids": [12]},
            }
        )
        response = self.request_executor({"vote_delegated_to_ids": [13]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User 4 cannot delegate his vote to user(s) [3], because these users have delegated their votes themselves.",
            response.json["message"],
        )

    def test_delegated_replace_existing_to_other_user(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_ids": [13]},
                "meeting_user/14": {"vote_delegated_to_ids": [13]},
            }
        )
        response = self.request_executor({"vote_delegated_to_ids": [11]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegations_from_ids": [14]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_ids": [13]})
        self.assert_model_exists("meeting_user/13", {"vote_delegations_from_ids": [12]})
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_ids": [11]})

    def test_delegated_to_multiple_users_limit_1_error(self) -> None:
        response = self.request_executor({"vote_delegated_to_ids": [11, 13]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User 4 cannot delegate his vote to more than 1 user in meeting 222.",
            response.json["message"],
        )

    def test_delegated_to_multiple_users_limit_2_error(self) -> None:
        self.set_models(
            {
                "meeting/222": {"users_vote_delegations_max_amount": 2},
                "group/224": {"meeting_user_ids": [11, 12, 13, 14, 15]},
                "user/5": {"username": "user5"},
                "meeting_user/15": {"meeting_id": 222, "user_id": 5},
            }
        )
        response = self.request_executor({"vote_delegated_to_ids": [11, 13, 15]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User 4 cannot delegate his vote to more than 2 users in meeting 222.",
            response.json["message"],
        )

    def test_delegated_from_multiple_users_limit_1_error(self) -> None:
        response = self.request_executor({"vote_delegations_from_ids": [11, 12]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User(s) [2] cannot delegate their votes to more than 1 user in meeting 222.",
            response.json["message"],
        )

    def test_delegated_from_multiple_users_limit_2_error(self) -> None:
        self.set_models(
            {
                "meeting/222": {"users_vote_delegations_max_amount": 2},
                "group/224": {"meeting_user_ids": [11, 12, 13, 14, 15]},
                "user/5": {"username": "user5"},
                "meeting_user/15": {"meeting_id": 222, "user_id": 5},
                "meeting_user/12": {"vote_delegated_to_ids": [13, 15]},
            }
        )
        response = self.request_executor({"vote_delegations_from_ids": [11, 12]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User(s) [2] cannot delegate their votes to more than 2 users in meeting 222.",
            response.json["message"],
        )

    def test_vote_add_1_remove_other_2_from_standard_user(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting_user/11": {"vote_delegated_to_ids": [14]},
                "meeting_user/12": {"vote_delegated_to_ids": [14]},
            }
        )

        response = self.request_executor({"vote_delegations_from_ids": [13]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegated_to_ids": None})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_ids": None})
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_ids": [14]})
        self.assert_model_exists("meeting_user/14", {"vote_delegations_from_ids": [13]})

    def test_delegations_from_but_delegated_own(self) -> None:
        self.set_models({"meeting_user/14": {"vote_delegated_to_ids": [13]}})
        response = self.request_executor({"vote_delegations_from_ids": [11]})

        self.assert_status_code(response, 400)
        self.assertEqual(
            "User 4 cannot receive vote delegations, because he delegated his own vote.",
            response.json["message"],
        )

    def test_delegations_from_target_user_receives_delegations(self) -> None:
        response = self.request_executor({"vote_delegations_from_ids": [13]})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User(s) [3] can't delegate their votes because they receive vote delegations.",
            response.json["message"],
        )

    def test_vote_setting_both_correct_from_to_1_standard_user(self) -> None:
        """meeting_user2/4 -> meeting_user3: meeting_user4 reset own delegation and receives other delegation"""
        self.set_models({"meeting_user/14": {"vote_delegated_to_ids": [13]}})

        response = self.request_executor(
            {"vote_delegations_from_ids": [11], "vote_delegated_to_ids": []}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegated_to_ids": [14]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_ids": [13]})
        self.assert_model_exists("meeting_user/13", {"vote_delegations_from_ids": [12]})
        self.assert_model_exists(
            "meeting_user/14",
            {"vote_delegated_to_ids": None, "vote_delegations_from_ids": [11]},
        )

    def test_vote_setting_both_correct_from_to_2_standard_user(self) -> None:
        """meeting_user2/3 -> meeting_user4: meeting_user4 delegates to meeting_user/1 and resets it's received delegations"""
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_ids": [14]},
                "meeting_user/13": {"vote_delegated_to_ids": [14]},
            }
        )

        response = self.request_executor(
            {"vote_delegations_from_ids": [], "vote_delegated_to_ids": [11]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegations_from_ids": [14]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_ids": None})
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_ids": None})
        self.assert_model_exists("meeting_user/14", {"vote_delegated_to_ids": [11]})

    def test_vote_setting_both_from_to_error_standard_user_1(self) -> None:
        """meeting_user2/3 -> meeting_user4: meeting_user4 delegates to meeting_user/13 and resets received delegation from meeting_user/13"""
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_ids": [14]},
                "meeting_user/13": {"vote_delegated_to_ids": [14]},
            }
        )
        response = self.request_executor(
            {"vote_delegations_from_ids": [12], "vote_delegated_to_ids": [13]}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "User 4 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )

    def test_vote_add_remove_delegations_from_standard_user_ok(self) -> None:
        """user2/3 -> user4: user4 removes 2 and adds 1 delegations_from"""
        self.set_models(
            {
                "meeting_user/12": {"vote_delegated_to_ids": [14]},
                "meeting_user/13": {"vote_delegated_to_ids": [14]},
            }
        )
        response = self.request_executor({"vote_delegations_from_ids": [13, 11]})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/14", {"vote_delegations_from_ids": [11, 13]}
        )
        self.assert_model_exists("meeting_user/13", {"vote_delegated_to_ids": [14]})
        self.assert_model_exists("meeting_user/11", {"vote_delegated_to_ids": [14]})
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_ids": None})

    def test_delegate_and_redelegate_in_1_request_ok(self) -> None:
        response = self.request_multi(
            "meeting_user.set_data",
            [
                {
                    "id": 12,
                    "vote_delegated_to_ids": [14],
                },
                {
                    "id": 12,
                    "vote_delegated_to_ids": [11],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/12",
            {"vote_delegated_to_ids": [11]},
        )
        for id_ in [13, 14]:
            self.assert_model_exists(
                f"meeting_user/{id_}",
                {"vote_delegations_from_ids": None},
            )
        self.assert_model_exists(
            "meeting_user/11",
            {"vote_delegations_from_ids": [12]},
        )

    def test_delegate_and_add_delegation_in_1_request_ok(self) -> None:
        self.set_models({"meeting/222": {"users_vote_delegations_max_amount": 2}})
        response = self.request_multi(
            "meeting_user.set_data",
            [
                {
                    "id": 12,
                    "vote_delegated_to_ids": [14],
                },
                {
                    "id": 12,
                    "vote_delegated_to_ids": [14, 11],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/12",
            {"vote_delegated_to_ids": [11, 14]},
        )
        for id_ in [11, 14]:
            self.assert_model_exists(
                f"meeting_user/{id_}",
                {"vote_delegations_from_ids": [12]},
            )
        self.assert_model_exists(
            "meeting_user/13",
            {"vote_delegations_from_ids": None},
        )

    def test_receive_delegations_from_2_users_1_request_ok(self) -> None:
        self.set_models({"meeting_user/12": {"vote_delegated_to_ids": None}})
        response = self.request_multi(
            "meeting_user.set_data",
            [
                {
                    "id": 12,
                    "vote_delegations_from_ids": [13],
                },
                {
                    "id": 12,
                    "vote_delegations_from_ids": [11],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/12", {"vote_delegations_from_ids": [11, 13]}
        )
        for id_ in [11, 13]:
            self.assert_model_exists(
                f"meeting_user/{id_}", {"vote_delegated_to_ids": [12]}
            )

    def test_receive_delegations_reverse_from_2_users_1_request_ok(self) -> None:
        response = self.request_multi(
            "meeting_user.set_data",
            [
                {
                    "id": 12,
                    "vote_delegated_to_ids": [14],
                },
                {
                    "id": 13,
                    "vote_delegated_to_ids": [14],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/14", {"vote_delegations_from_ids": [12, 13]}
        )
        self.assert_model_exists("meeting_user/12", {"vote_delegated_to_ids": [14]})
        self.assert_model_exists(
            "meeting_user/13",
            {
                "vote_delegated_to_ids": [14],
                "vote_delegations_from_ids": None,
            },
        )

    def test_delegate_reverse_to_2_users_1_request_ok(self) -> None:
        self.set_models({"meeting/222": {"users_vote_delegations_max_amount": 3}})
        response = self.request_multi(
            "meeting_user.set_data",
            [
                {
                    "id": 11,
                    "vote_delegations_from_ids": [12],
                },
                {
                    "id": 14,
                    "vote_delegations_from_ids": [12],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/12", {"vote_delegated_to_ids": [11, 13, 14]}
        )
        for id_ in [11, 13, 14]:
            self.assert_model_exists(
                f"meeting_user/{id_}", {"vote_delegations_from_ids": [12]}
            )
