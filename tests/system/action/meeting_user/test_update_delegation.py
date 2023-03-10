from typing import Any, Dict

from tests.system.action.base import BaseActionTestCase


class UserUpdateDelegationActionTest(BaseActionTestCase):
    def setup_base(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "Meeting222",
                    "is_active_in_organization_id": 1,
                },
                "meeting/223": {
                    "name": "Meeting223",
                    "is_active_in_organization_id": 1,
                },
                "group/1": {"meeting_id": 222, "meeting_user_ids": [1, 2, 3, 4]},
                "group/100": {"meeting_id": 223, "meeting_user_ids": [5]},
                "user/4": {
                    "username": "delegator2",
                    "meeting_ids": [222],
                    "meeting_user_ids": [4],
                },
                "user/5": {
                    "username": "user5",
                    "meeting_ids": [223],
                    "meeting_user_ids": [5],
                },
                "meeting_user/4": {
                    "meeting_id": 222,
                    "user_id": 4,
                    "vote_delegated_to_id": 2,
                    "group_ids": [1],
                },
                "meeting_user/5": {
                    "meeting_id": 223,
                    "user_id": 5,
                    "group_ids": [100],
                },
            }
        )

    def setup_vote_delegation(self) -> None:
        self.setup_base()
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [222],
                },
                "user/2": {
                    "username": "voter",
                    "meeting_ids": [222],
                    "meeting_user_ids": [2],
                },
                "user/3": {
                    "username": "delegator1",
                    "meeting_ids": [222],
                    "meeting_user_ids": [3],
                },
                "meeting_user/1": {"meeting_id": 222, "user_id": 1, "group_ids": [1]},
                "meeting_user/2": {
                    "meeting_id": 222,
                    "user_id": 2,
                    "vote_delegations_from_ids": [3, 4],
                    "group_ids": [1],
                },
                "meeting_user/3": {
                    "meeting_id": 222,
                    "user_id": 3,
                    "vote_delegated_to_id": 2,
                    "group_ids": [1],
                },
            },
        )

    def test_update_simple_delegated_to_standard_user(self) -> None:
        """meeting_user/2 with permission delegates to admin meeting_user/1"""
        setup_data: Dict[str, Dict[str, Any]] = {
            "user/2": {
                "meeting_ids": [222],
            },
            "meeting_user/2": {
                "meeting_id": 222,
                "user_id": 2,
                "group_ids": [1],
            },
        }
        request_data = {"id": 2, "vote_delegated_to_id": 1}
        self.set_models(
            {
                "meeting/222": {
                    "name": "Meeting222",
                    "is_active_in_organization_id": 1,
                },
                "group/1": {"meeting_id": 222, "meeting_user_ids": [1, 2]},
                "user/1": {
                    "meeting_ids": [222],
                },
                "meeting_user/1": {
                    "meeting_id": 222,
                    "user_id": 1,
                    "group_ids": [1],
                },
            }
        )
        self.set_models(setup_data)
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1",
            {"vote_delegations_from_ids": [2]},
        )
        self.assert_model_exists(
            "meeting_user/2",
            {"vote_delegated_to_id": 1},
        )

    def test_update_vote_delegated_to_self_standard_user(self) -> None:
        """meeting_user/2 tries to delegate to himself"""
        setup_data: Dict[str, Dict[str, Any]] = {
            "user/2": {
                "meeting_ids": [222],
                "meeting_user_ids": [2],
            },
            "meeting_user/2": {"meeting_id": 222, "user_id": 2, "group_ids": [1]},
        }
        request_data = {"id": 2, "vote_delegated_to_id": 2}
        self.set_models(
            {
                "meeting/222": {
                    "name": "Meeting222",
                    "is_active_in_organization_id": 1,
                },
                "group/1": {"meeting_id": 222, "meeting_user_ids": [2]},
            },
        )
        self.set_models(setup_data)
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 2 can't delegate the vote to himself.", response.json["message"]
        )

    def test_update_vote_delegated_to_invalid_id_standard_user(self) -> None:
        """meeting_user/2 tries to delegate to not existing meeting_user/42"""
        setup_data: Dict[str, Dict[str, Any]] = {
            "user/2": {"meeting_user_ids": [2]},
            "meeting_user/2": {"meeting_id": 222, "user_id": 2, "group_ids": [1]},
        }

        request_data = {"id": 2, "vote_delegated_to_id": 42}
        self.set_models(
            {
                "meeting/222": {
                    "name": "Meeting222",
                    "is_active_in_organization_id": 1,
                },
                "group/1": {"meeting_id": 222, "meeting_user_ids": [2]},
            },
        )
        self.set_models(setup_data)
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "meeting_user/42' does not exist.",
            response.json["message"],
        )

    def test_update_vote_delegations_from_self_standard_user(self) -> None:
        """meeting_user/2 tries to delegate to himself"""
        setup_data: Dict[str, Dict[str, Any]] = {
            "user/2": {
                "meeting_ids": [222],
                "meeting_user_ids": [2],
            },
            "meeting_user/2": {
                "meeting_id": 222,
                "user_id": 2,
                "group_ids": [1],
            },
        }
        request_data = {"id": 2, "vote_delegations_from_ids": [2]}
        self.set_models(
            {
                "meeting/222": {
                    "name": "Meeting222",
                    "is_active_in_organization_id": 1,
                },
                "group/1": {"meeting_id": 222, "meeting_user_ids": [2]},
            },
        )
        self.set_models(setup_data)
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 2 can't delegate the vote to himself.", response.json["message"]
        )

    def test_update_vote_delegations_from_invalid_id_standard_user(self) -> None:
        """meeting_user/2 receives delegation from non existing meeting_user/1234"""
        setup_data: Dict[str, Dict[str, Any]] = {
            "user/2": {"meeting_user_ids": [2]},
            "meeting_user/2": {"meeting_id": 222, "user_id": 2, "group_ids": [1]},
        }
        request_data = {"id": 2, "vote_delegations_from_ids": [1234]}
        self.set_models(
            {
                "meeting/222": {
                    "name": "Meeting222",
                    "is_active_in_organization_id": 1,
                },
                "group/1": {"meeting_id": 222, "meeting_user_ids": [2]},
            },
        )
        self.set_models(setup_data)
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model 'meeting_user/1234' does not exist.",
            response.json["message"],
        )

    def test_update_reset_vote_delegated_to_standard_user(self) -> None:
        """meeting_user/3->meeting_user/2: meeting_user/3 wants to reset delegation to meeting_user/2"""
        request_data = {"id": 3, "vote_delegated_to_id": None}
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/2",
            {
                "vote_delegations_from_ids": [4],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "vote_delegated_to_id": None,
            },
        )

    def test_update_reset_vote_delegations_from_standard_user(self) -> None:
        """meeting_user/3/4->meeting_user/2: meeting_user/2 wants to reset delegation from meeting_user/3"""
        request_data = {"id": 2, "vote_delegations_from_ids": [4]}
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/2",
            {
                "vote_delegations_from_ids": [4],
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_to_id": None,
            },
        )

    def test_update_vote_delegations_from_on_empty_array_standard_user(self) -> None:
        """meeting_user/3/4->meeting_user/2: meeting_user/2 wants to reset all delegations"""
        request_data = {"id": 2, "vote_delegations_from_ids": []}
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_from_ids": None,
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_to_id": None,
            },
        )

    def test_update_nested_vote_delegated_to_1_standard_user(self) -> None:
        """meeting_user3 -> meeting_user2: meeting_user/2 wants to delegate to meeting_user/1"""
        request_data = {"id": 2, "vote_delegated_to_id": 1}
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "MeetingUser 2 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "vote_delegations_from_ids": [3, 4],
            },
        )

    def test_update_nested_vote_delegated_to_2_standard_user(self) -> None:
        """meeting_user3 -> meeting_user2: meeting_user/1 wants to delegate to meeting_user/3"""
        request_data = {"id": 1, "vote_delegated_to_id": 3}
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "MeetingUser 1 cannot delegate his vote to user 3, because that user has delegated his vote himself.",
            response.json["message"],
        )

    def test_update_vote_delegated_replace_existing_to_standard_user(self) -> None:
        """meeting_user3->meeting_user/2: meeting_user/3 wants to delegate to meeting_user/1 instead to meeting_user/2"""
        request_data = {"id": 3, "vote_delegated_to_id": 1}
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", {"vote_delegations_from_ids": [3]})
        self.assert_model_exists("meeting_user/2", {"vote_delegations_from_ids": [4]})
        self.assert_model_exists("meeting_user/3", {"vote_delegated_to_id": 1})
        self.assert_model_exists("meeting_user/4", {"vote_delegated_to_id": 2})

    def test_update_vote_delegated_replace_existing_to_2_standard_user(self) -> None:
        """meeting_user3->meeting_user/2: meeting_user/3 wants to delegate to meeting_user/1 instead to meeting_user/2"""
        request_data = {"id": 3, "vote_delegated_to_id": 1}
        self.setup_vote_delegation()
        self.set_models(
            {
                "user/1": {
                    "meeting_ids": [222],
                    "meeting_user_ids": [1],
                },
                "user/5": {
                    "username": "delegator5",
                    "meeting_ids": [222],
                    "meeting_user_ids": [5],
                },
                "meeting_user/1": {
                    "vote_delegations_from_ids": [5],
                },
                "meeting_user/5": {
                    "meeting_id": 222,
                    "user_id": 5,
                    "vote_delegated_to_id": 1,
                },
            }
        )

        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1", {"vote_delegations_from_ids": [5, 3]}
        )
        self.assert_model_exists("meeting_user/2", {"vote_delegations_from_ids": [4]})
        self.assert_model_exists("meeting_user/3", {"vote_delegated_to_id": 1})
        self.assert_model_exists("meeting_user/4", {"vote_delegated_to_id": 2})
        self.assert_model_exists("meeting_user/5", {"vote_delegated_to_id": 1})

    def test_update_vote_replace_existing_delegations_from_standard_user(self) -> None:
        """meeting_user3->meeting_user/2: meeting_user/3 wants to delegate to meeting_user/1 instead to meeting_user/2"""
        request_data = {"id": 1, "vote_delegations_from_ids": [5, 3]}
        self.setup_vote_delegation()
        self.set_models(
            {
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [222],
                },
                "user/5": {
                    "username": "delegator5",
                    "meeting_ids": [222],
                    "meeting_user_ids": [5],
                },
                "meeting_user/1": {
                    "vote_delegations_from_ids": [5],
                },
                "meeting_user/5": {
                    "meeting_id": 222,
                    "user_id": 5,
                    "vote_delegated_to_id": 1,
                    "group_ids": [1],
                },
            }
        )

        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1",
            {
                "vote_delegations_from_ids": [5, 3],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "vote_delegations_from_ids": [4],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "vote_delegated_to_id": 1,
            },
        )
        self.assert_model_exists(
            "meeting_user/4",
            {
                "vote_delegated_to_id": 2,
            },
        )
        self.assert_model_exists(
            "meeting_user/5",
            {
                "vote_delegated_to_id": 1,
            },
        )

    def test_update_vote_add_1_remove_other_delegations_from_standard_user(
        self,
    ) -> None:
        """meeting_user3/4 -> meeting_user2: delegate meeting_user/1 to meeting_user/2 and remove meeting_user/3 and 4"""
        request_data = {"id": 2, "vote_delegations_from_ids": [1]}
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1",
            {"vote_delegated_to_id": 2},
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "vote_delegations_from_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "vote_delegated_to_id": None,
            },
        )

    def test_update_vote_delegations_from_nested_1_standard_user(self) -> None:
        """meeting_user3-> meeting_user2: admin tries to delegate to meeting_user/3"""
        request_data = {"id": 3, "vote_delegations_from_ids": [1]}
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)

        self.assert_status_code(response, 400)
        self.assertIn(
            "MeetingUser 3 cannot receive vote delegations, because he delegated his own vote.",
            response.json["message"],
        )

    def test_update_vote_delegations_from_nested_2_standard_user(self) -> None:
        """meeting_user3 -> meeting_user2: meeting_user2 tries to delegate to admin"""
        request_data = {"id": 1, "vote_delegations_from_ids": [2]}

        self.setup_vote_delegation()

        response = self.request("meeting_user.update", request_data)

        self.assert_status_code(response, 400)
        self.assertIn(
            "MeetingUser(s) [2] can't delegate their votes because they receive vote delegations.",
            response.json["message"],
        )

    def test_update_vote_setting_both_correct_from_to_1_standard_user(self) -> None:
        """meeting_user3/4 -> meeting_user2: meeting_user3 reset own delegation and receives other delegation"""
        request_data = {
            "id": 3,
            "vote_delegations_from_ids": [1],
            "vote_delegated_to_id": None,
        }
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1",
            {
                "vote_delegated_to_id": 3,
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "vote_delegations_from_ids": [4],
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "vote_delegated_to_id": None,
                "vote_delegations_from_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/4",
            {"vote_delegated_to_id": 2},
        )

    def test_update_vote_setting_both_correct_from_to_2_standard_user(self) -> None:
        """meeting_user3/4 -> meeting_user2: meeting_user2 delegates to meeting_user/1 and resets it's received delegations"""
        request_data = {
            "id": 2,
            "vote_delegations_from_ids": [],
            "vote_delegated_to_id": 1,
        }
        self.setup_vote_delegation()

        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/2",
            {
                "vote_delegated_to_id": 1,
                "vote_delegations_from_ids": [],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "vote_delegations_from_ids": [2],
            },
        )

    def test_update_vote_setting_both_from_to_error_standard_user_1(self) -> None:
        """meeting_user3/4 -> meeting_user2: meeting_user2 delegates to meeting_user/3 and resets received delegation from meeting_user/3"""
        request_data = {
            "id": 2,
            "vote_delegations_from_ids": [4],
            "vote_delegated_to_id": 3,
        }
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)

        self.assert_status_code(response, 400)
        self.assertIn(
            "User 2 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )

    def test_update_vote_setting_both_from_to_error_standard_user_2(self) -> None:
        """new meeting_user/100 without vote delegation dependencies tries to delegate from and to at the same time"""
        self.set_models(
            {
                "user/100": {
                    "username": "new independant",
                    "meeting_ids": [222],
                },
                "meeting_user/100": {
                    "meeting_id": 222,
                    "user_id": 100,
                    "group_ids": [1],
                },
            },
        )
        request_data = {
            "id": 100,
            "vote_delegations_from_ids": [1],
            "vote_delegated_to_id": 1,
        }
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "MeetingUser 100 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )

    def test_update_vote_add_remove_delegations_from_standard_user(self) -> None:
        """meeting_user3/4 -> meeting_user2: meeting_user2 removes 4 and adds 1 delegations_from"""
        request_data = {"id": 2, "vote_delegations_from_ids": [3, 1]}
        self.setup_vote_delegation()
        response = self.request("meeting_user.update", request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", {"vote_delegated_to_id": 2})
        meeting_user2 = self.get_model("meeting_user/2")
        self.assertCountEqual(meeting_user2["vote_delegations_from_ids"], [1, 3])
        self.assert_model_exists("meeting_user/3", {"vote_delegated_to_id": 2})
        meeting_user4 = self.get_model("meeting_user/4")
        self.assertIn(meeting_user4.get("vote_delegated_to_id"), (None, []))
