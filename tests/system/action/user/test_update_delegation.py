from typing import Any, Dict

from tests.system.action.base import BaseActionTestCase


class UserUpdateDelegationActionTest(BaseActionTestCase):
    def setup_base(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "meeting/223": {"name": "Meeting223"},
                "group/1": {"meeting_id": 222, "user_ids": [1, 2, 3, 4]},
                "group/100": {"meeting_id": 223, "user_ids": [5]},
                "user/4": {
                    "username": "delegator2",
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                    "vote_delegated_$222_to_id": 2,
                    "vote_delegated_$_to_id": ["222"],
                },
                "user/5": {
                    "username": "user5",
                    "group_$_ids": ["223"],
                    "group_$223_ids": [100],
                },
            }
        )

    def setup_vote_delegation(self) -> None:
        self.setup_base()
        self.set_models(
            {
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "username": "voter",
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                    "vote_delegations_$222_from_ids": [3, 4],
                    "vote_delegations_$_from_ids": ["222"],
                },
                "user/3": {
                    "username": "delegator1",
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                    "vote_delegated_$222_to_id": 2,
                    "vote_delegated_$_to_id": ["222"],
                },
            },
        )

    def setup_vote_delegation_temporary(self) -> None:
        self.setup_base()
        self.set_models(
            {
                "user/1": {"meeting_id": 222},
                "user/2": {
                    "username": "voter",
                    "meeting_id": 222,
                    "vote_delegations_$222_from_ids": [3, 4],
                    "vote_delegations_$_from_ids": ["222"],
                },
                "user/3": {
                    "username": "delegator1",
                    "meeting_id": 222,
                    "vote_delegated_$222_to_id": 2,
                    "vote_delegated_$_to_id": ["222"],
                },
            },
        )

    def test_update_simple_delegated_to_standard_user(self) -> None:
        setup_data = {"user/2": {"group_$_ids": ["222"], "group_$222_ids": [1]}}
        request_data = {"id": 2, "vote_delegated_$_to_id": {222: 1}}
        self.t_update_simple_delegated_to("user.update", setup_data, request_data)

    def test_update_simple_delegated_to_temporary_user(self) -> None:
        setup_data = {"user/2": {"meeting_id": 222}}
        request_data = {"id": 2, "vote_delegated_to_id": 1}
        self.t_update_simple_delegated_to(
            "user.update_temporary", setup_data, request_data
        )

    def t_update_simple_delegated_to(
        self, action: str, setup_data: Dict[str, Any], request_data: Dict[str, Any]
    ) -> None:
        """ user/2 with permission delegates to admin user/1 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1, 2]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
            }
        )
        self.set_models(setup_data)
        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "vote_delegations_$222_from_ids": [2],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/2",
            {"vote_delegated_$222_to_id": 1, "vote_delegated_$_to_id": ["222"]},
        )

    def test_update_vote_delegated_to_self_standard_user(self) -> None:
        setup_data = {"user/2": {"group_$_ids": ["222"], "group_$222_ids": [1]}}
        request_data = {"id": 2, "vote_delegated_$_to_id": {222: 2}}
        self.t_update_vote_delegated_to_self("user.update", setup_data, request_data)

    def test_update_vote_delegated_to_self_temporary_user(self) -> None:
        setup_data = {"user/2": {"meeting_id": 222}}
        request_data = {"id": 2, "vote_delegated_to_id": 2}
        self.t_update_vote_delegated_to_self(
            "user.update_temporary", setup_data, request_data
        )

    def t_update_vote_delegated_to_self(
        self, action: str, setup_data: Dict[str, Any], request_data: Dict[str, Any]
    ) -> None:
        """ user/2 tries to delegate to himself """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [2]},
            },
        )
        self.set_models(setup_data)
        response = self.request(action, request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 2 can't delegate the vote to himself.", response.json["message"]
        )

    def test_update_vote_delegated_to_invalid_id_standard_user(self) -> None:
        setup_data = {"user/2": {"group_$_ids": ["222"], "group_$222_ids": [1]}}
        request_data = {"id": 2, "vote_delegated_$_to_id": {222: 42}}
        self.t_update_vote_delegated_to_invalid_id(
            "user.update", setup_data, request_data
        )

    def test_update_vote_delegated_to_invalid_id_temporary_user(self) -> None:
        setup_data = {"user/2": {"meeting_id": 222}}
        request_data = {"id": 2, "vote_delegated_to_id": 42}
        self.t_update_vote_delegated_to_invalid_id(
            "user.update_temporary", setup_data, request_data
        )

    def t_update_vote_delegated_to_invalid_id(
        self, action: str, setup_data: Dict[str, Any], request_data: Dict[str, Any]
    ) -> None:
        """ User/2 tries to delegate to not existing user/42 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [2]},
            },
        )
        self.set_models(setup_data)
        response = self.request(action, request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following users were not found: {42}",
            response.json["message"],
        )

    def test_update_vote_delegations_from_self_standard_user(self) -> None:
        setup_data = {"user/2": {"group_$_ids": ["222"], "group_$222_ids": [1]}}
        request_data = {"id": 2, "vote_delegations_$_from_ids": {222: [2]}}
        self.t_update_vote_delegations_from_self(
            "user.update", setup_data, request_data
        )

    def test_update_vote_delegations_from_self_temporary_user(self) -> None:
        setup_data = {"user/2": {"meeting_id": 222}}
        request_data = {"id": 2, "vote_delegations_from_ids": [2]}
        self.t_update_vote_delegations_from_self(
            "user.update_temporary", setup_data, request_data
        )

    def t_update_vote_delegations_from_self(
        self, action: str, setup_data: Dict[str, Any], request_data: Dict[str, Any]
    ) -> None:
        """ user/2 tries to delegate to himself """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [2]},
            },
        )
        self.set_models(setup_data)
        response = self.request(action, request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 2 can't delegate the vote to himself.", response.json["message"]
        )

    def test_update_vote_delegations_from_invalid_id_standard_user(self) -> None:
        setup_data = {"user/2": {"group_$_ids": ["222"], "group_$222_ids": [1]}}
        request_data = {"id": 2, "vote_delegations_$_from_ids": {222: [1234]}}
        self.t_update_vote_delegations_from_invalid_id(
            "user.update", setup_data, request_data
        )

    def test_update_vote_delegations_from_invalid_id_temporary_user(self) -> None:
        setup_data = {"user/2": {"meeting_id": 222}}
        request_data = {"id": 2, "vote_delegations_from_ids": [1234]}
        self.t_update_vote_delegations_from_invalid_id(
            "user.update_temporary", setup_data, request_data
        )

    def t_update_vote_delegations_from_invalid_id(
        self, action: str, setup_data: Dict[str, Any], request_data: Dict[str, Any]
    ) -> None:
        """ user/2 receives delegation from non existing user/1234 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [2]},
                "user/2": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
            },
        )
        self.set_models(setup_data)
        response = self.request(action, request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following users were not found: {1234}",
            response.json["message"],
        )

    def test_update_reset_vote_delegated_to_standard_user(self) -> None:
        request_data = {"id": 3, "vote_delegated_$_to_id": {222: None}}
        self.t_update_reset_vote_delegated_to("user.update", request_data)

    def test_update_reset_vote_delegated_to_temporary_user(self) -> None:
        request_data = {"id": 3, "vote_delegated_to_id": None}
        self.t_update_reset_vote_delegated_to("user.update_temporary", request_data)

    def t_update_reset_vote_delegated_to(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user/3->user/2: user/3 wants to reset delegation to user/2"""
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()
        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [4],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_$222_to_id": None,
                "vote_delegated_$_to_id": [],
            },
        )

    def test_update_reset_vote_delegations_from_standard_user(self) -> None:
        request_data = {"id": 2, "vote_delegations_$_from_ids": {222: [4]}}
        self.t_update_reset_vote_delegations_from("user.update", request_data)

    def test_update_reset_vote_delegations_from_temporary_user(self) -> None:
        request_data = {"id": 2, "vote_delegations_from_ids": [4]}
        self.t_update_reset_vote_delegations_from("user.update_temporary", request_data)

    def t_update_reset_vote_delegations_from(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user/3/4->user/2: user/2 wants to reset delegation from user/3"""
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()
        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [4],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_$222_to_id": None,
                "vote_delegated_$_to_id": [],
            },
        )

    def test_update_vote_delegations_from_on_empty_array_standard_user(self) -> None:
        request_data = {"id": 2, "vote_delegations_$_from_ids": {222: []}}
        self.t_update_vote_delegations_from_on_empty_array("user.update", request_data)

    def test_update_vote_delegations_from_on_empty_array_temporary_user(self) -> None:
        request_data = {"id": 2, "vote_delegations_from_ids": []}
        self.t_update_vote_delegations_from_on_empty_array(
            "user.update_temporary", request_data
        )

    def t_update_vote_delegations_from_on_empty_array(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user/3/4->user/2: user/2 wants to reset all delegations"""
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()
        response = self.request(action, request_data)

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_$222_to_id": None,
                "vote_delegated_$_to_id": [],
            },
        )

    def test_update_nested_vote_delegated_to_1_standard_user(self) -> None:
        request_data = {"id": 2, "vote_delegated_$_to_id": {222: 1}}
        self.t_update_nested_vote_delegated_to_1("user.update", request_data)

    def test_update_nested_vote_delegated_to_1_temporary_user(self) -> None:
        request_data = {"id": 2, "vote_delegated_to_id": 1}
        self.t_update_nested_vote_delegated_to_1("user.update_temporary", request_data)

    def t_update_nested_vote_delegated_to_1(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3 -> user2: user/2 wants to delegate to user/1 """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()
        response = self.request(action, request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 2 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegated_$222_to_id": None,
                "vote_delegations_$222_from_ids": [3, 4],
            },
        )

    def test_update_nested_vote_delegated_to_2_standard_user(self) -> None:
        request_data = {"id": 1, "vote_delegated_$_to_id": {222: 3}}
        self.t_update_nested_vote_delegated_to_2("user.update", request_data)

    def test_update_nested_vote_delegated_to_2_temporary_user(self) -> None:
        request_data = {"id": 1, "vote_delegated_to_id": 3}
        self.t_update_nested_vote_delegated_to_2("user.update_temporary", request_data)

    def t_update_nested_vote_delegated_to_2(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3 -> user2: user/1 wants to delegate to user/3 """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()
        response = self.request(action, request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1 cannot delegate his vote to user 3, because that user has delegated his vote himself.",
            response.json["message"],
        )

    def test_update_vote_delegated_replace_existing_to_standard_user(self) -> None:
        request_data = {"id": 3, "vote_delegated_$_to_id": {222: 1}}
        self.t_update_vote_delegated_replace_existing_to("user.update", request_data)

    def test_update_vote_delegated_replace_existing_to_temporary_user(self) -> None:
        request_data = {"id": 3, "vote_delegated_to_id": 1}
        self.t_update_vote_delegated_replace_existing_to(
            "user.update_temporary", request_data
        )

    def t_update_vote_delegated_replace_existing_to(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3->user/2: user/3 wants to delegate to user/1 instead to user/2 """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()

        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"vote_delegations_$222_from_ids": [3]})
        self.assert_model_exists("user/2", {"vote_delegations_$222_from_ids": [4]})
        self.assert_model_exists("user/3", {"vote_delegated_$222_to_id": 1})
        self.assert_model_exists("user/4", {"vote_delegated_$222_to_id": 2})

    def test_update_vote_delegated_replace_existing_to_2_standard_user(self) -> None:
        request_data = {"id": 3, "vote_delegated_$_to_id": {222: 1}}
        self.t_update_vote_delegated_replace_existing_to_2("user.update", request_data)

    def test_update_vote_delegated_replace_existing_to_2_temporary_user(self) -> None:
        request_data = {"id": 3, "vote_delegated_to_id": 1}
        self.t_update_vote_delegated_replace_existing_to_2(
            "user.update_temporary", request_data
        )

    def t_update_vote_delegated_replace_existing_to_2(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3->user/2: user/3 wants to delegate to user/1 instead to user/2 """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()
        self.set_models(
            {
                "user/1": {
                    "meeting_id": 222,
                    "vote_delegations_$222_from_ids": [5],
                    "vote_delegations_$_from_ids": ["222"],
                },
                "user/5": {
                    "username": "delegator5",
                    "meeting_id": 222,
                    "vote_delegated_$222_to_id": 1,
                    "vote_delegated_$_to_id": ["222"],
                },
            }
        )

        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"vote_delegations_$222_from_ids": [5, 3]})
        self.assert_model_exists("user/2", {"vote_delegations_$222_from_ids": [4]})
        self.assert_model_exists("user/3", {"vote_delegated_$222_to_id": 1})
        self.assert_model_exists("user/4", {"vote_delegated_$222_to_id": 2})
        self.assert_model_exists("user/5", {"vote_delegated_$222_to_id": 1})

    def test_update_vote_replace_existing_delegations_from_standard_user(self) -> None:
        request_data = {"id": 1, "vote_delegations_$_from_ids": {222: [5, 3]}}
        self.t_update_vote_replace_existing_delegations_from(
            "user.update", request_data
        )

    def test_update_vote_replace_existing_delegations_from_temporary_user(self) -> None:
        request_data = {"id": 1, "vote_delegations_from_ids": [5, 3]}
        self.t_update_vote_replace_existing_delegations_from(
            "user.update_temporary", request_data
        )

    def t_update_vote_replace_existing_delegations_from(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3->user/2: user/3 wants to delegate to user/1 instead to user/2 """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()
        self.set_models(
            {
                "user/1": {
                    "vote_delegations_$222_from_ids": [5],
                    "vote_delegations_$_from_ids": ["222"],
                },
                "user/5": {
                    "username": "delegator5",
                    "meeting_id": None,
                    "group_$222_ids": [1],
                    "group_$_ids": ["222"],
                    "vote_delegated_$222_to_id": 1,
                    "vote_delegated_$_to_id": ["222"],
                },
            }
        )

        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "vote_delegations_$222_from_ids": [5, 3],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [4],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {"vote_delegated_$222_to_id": 1, "vote_delegated_$_to_id": ["222"]},
        )
        self.assert_model_exists(
            "user/4",
            {"vote_delegated_$222_to_id": 2, "vote_delegated_$_to_id": ["222"]},
        )
        self.assert_model_exists(
            "user/5",
            {"vote_delegated_$222_to_id": 1, "vote_delegated_$_to_id": ["222"]},
        )

    def test_update_vote_add_1_remove_other_delegations_from_standard_user(
        self,
    ) -> None:
        request_data = {"id": 2, "vote_delegations_$_from_ids": {222: [1]}}
        self.t_update_vote_add_1_remove_other_delegations_from(
            "user.update", request_data
        )

    def test_update_vote_add_1_remove_other_delegations_from_temporary_user(
        self,
    ) -> None:
        request_data = {"id": 2, "vote_delegations_from_ids": [1]}
        self.t_update_vote_add_1_remove_other_delegations_from(
            "user.update_temporary", request_data
        )

    def t_update_vote_add_1_remove_other_delegations_from(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3/4 -> user2: delegate user/1 to user/2 and remove user/3 and 4"""
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()

        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {"vote_delegated_$222_to_id": 2, "vote_delegated_$_to_id": ["222"]},
        )
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [1],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {"vote_delegated_$222_to_id": None, "vote_delegated_$_to_id": []},
        )

    def test_update_vote_delegations_from_nested_1_standard_user(self) -> None:
        request_data = {"id": 3, "vote_delegations_$_from_ids": {222: [1]}}
        self.t_update_vote_delegations_from_nested_1("user.update", request_data)

    def test_update_vote_delegations_from_nested_1_temporary_user(self) -> None:
        request_data = {"id": 3, "vote_delegations_from_ids": [1]}
        self.t_update_vote_delegations_from_nested_1(
            "user.update_temporary", request_data
        )

    def t_update_vote_delegations_from_nested_1(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3-> user2: admin tries to delegate to user/3 """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()

        response = self.request(action, request_data)

        self.assert_status_code(response, 400)
        self.assertIn(
            "User 3 cannot receive vote delegations, because he delegated his own vote.",
            response.json["message"],
        )

    def test_update_vote_delegations_from_nested_2_standard_user(self) -> None:
        request_data = {"id": 1, "vote_delegations_$_from_ids": {222: [2]}}
        self.t_update_vote_delegations_from_nested_2("user.update", request_data)

    def test_update_vote_delegations_from_nested_2_temporary_user(self) -> None:
        request_data = {"id": 1, "vote_delegations_from_ids": [2]}
        self.t_update_vote_delegations_from_nested_2(
            "user.update_temporary", request_data
        )

    def t_update_vote_delegations_from_nested_2(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3 -> user2: user2 tries to delegate to admin """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()

        response = self.request(action, request_data)

        self.assert_status_code(response, 400)
        self.assertIn(
            "User(s) [2] can't delegate their votes , because they receive vote delegations.",
            response.json["message"],
        )

    def test_update_vote_setting_both_correct_from_to_1_standard_user(self) -> None:
        request_data = {
            "id": 3,
            "vote_delegations_$_from_ids": {222: [1]},
            "vote_delegated_$_to_id": {222: None},
        }
        self.t_update_vote_setting_both_correct_from_to_1("user.update", request_data)

    def test_update_vote_setting_both_correct_from_to_1_temporary_user(self) -> None:
        request_data = {
            "id": 3,
            "vote_delegations_from_ids": [1],
            "vote_delegated_to_id": None,
        }
        self.t_update_vote_setting_both_correct_from_to_1(
            "user.update_temporary", request_data
        )

    def t_update_vote_setting_both_correct_from_to_1(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3/4 -> user2: user3 reset own delegation and receives other delegation """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()

        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {"vote_delegated_$222_to_id": 3, "vote_delegated_$_to_id": ["222"]},
        )
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [4],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_$_to_id": [],
                "vote_delegations_$222_from_ids": [1],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/4",
            {"vote_delegated_$222_to_id": 2, "vote_delegated_$_to_id": ["222"]},
        )

    def test_update_vote_setting_both_correct_from_to_2_standard_user(self) -> None:
        request_data = {
            "id": 2,
            "vote_delegations_$_from_ids": {222: []},
            "vote_delegated_$_to_id": {222: 1},
        }
        self.t_update_vote_setting_both_correct_from_to_2("user.update", request_data)

    def test_update_vote_setting_both_correct_from_to_2_temporary_user(self) -> None:
        request_data = {
            "id": 2,
            "vote_delegations_from_ids": [],
            "vote_delegated_to_id": 1,
        }
        self.t_update_vote_setting_both_correct_from_to_2(
            "user.update_temporary", request_data
        )

    def t_update_vote_setting_both_correct_from_to_2(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3/4 -> user2: user2 delegates to user/1 and resets it's received delegations """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()

        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegated_$222_to_id": 1,
                "vote_delegated_$_to_id": ["222"],
                "vote_delegations_$222_from_ids": [],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/1",
            {
                "vote_delegated_$_to_id": None,
                "vote_delegations_$222_from_ids": [2],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists("user/3", {"vote_delegated_$_to_id": []})
        self.assert_model_exists("user/4", {"vote_delegated_$_to_id": []})

    def test_update_vote_setting_both_from_to_error_standard_user_1(self) -> None:
        request_data = {
            "id": 2,
            "vote_delegations_$_from_ids": {222: [4]},
            "vote_delegated_$_to_id": {222: 3},
        }
        self.t_update_vote_setting_both_from_to_error_1("user.update", request_data)

    def test_update_vote_setting_both_from_to_error_temporary_user_1(self) -> None:
        request_data = {
            "id": 2,
            "vote_delegations_from_ids": [4],
            "vote_delegated_to_id": 3,
        }
        self.t_update_vote_setting_both_from_to_error_1(
            "user.update_temporary", request_data
        )

    def t_update_vote_setting_both_from_to_error_1(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3/4 -> user2: user2 delegates to user/3 and resets received delegation from user/3 """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()

        response = self.request(action, request_data)

        self.assert_status_code(response, 400)
        self.assertIn(
            "User 2 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )

    def test_update_vote_setting_both_from_to_error_standard_user_2(self) -> None:
        self.set_models({"user/100": {
                    "username": "new independant",
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                }},
        )
        request_data = {
            "id": 100,
            "vote_delegations_$_from_ids": {222: [1]},
            "vote_delegated_$_to_id": {222: 1},
        }
        self.t_update_vote_setting_both_from_to_2("user.update", request_data)

    def test_update_vote_setting_both_from_to_error_temporary_user_2(self) -> None:
        self.set_models({"user/100": {
                    "username": "new independant",
                    "meeting_id": 222,
                }},
        )
        request_data = {
            "id": 100,
            "vote_delegations_from_ids": [1],
            "vote_delegated_to_id": 1,
        }
        self.t_update_vote_setting_both_from_to_2(
            "user.update_temporary", request_data
        )

    def t_update_vote_setting_both_from_to_2(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ new user/100 without vote delegation dependencies tries to delegate from and to at the same time """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()

        response = self.request(action, request_data)
        self.assert_status_code(response, 400)
        self.assertIn('User 100 cannot delegate his vote, because there are votes delegated to him.', response.json["message"])

    def test_update_vote_add_remove_delegations_from_standard_user(self) -> None:
        request_data = {"id": 2, "vote_delegations_$_from_ids": {222: [3, 1]}}
        self.t_update_vote_add_remove_delegations_from("user.update", request_data)

    def test_update_vote_add_remove_delegations_from_temporary_user(self) -> None:
        request_data = {"id": 2, "vote_delegations_from_ids": [3, 1]}
        self.t_update_vote_add_remove_delegations_from(
            "user.update_temporary", request_data
        )

    def t_update_vote_add_remove_delegations_from(
        self, action: str, request_data: Dict[str, Any]
    ) -> None:
        """ user3/4 -> user2: user2 removes 4 and adds 1 delegations_from """
        if action == "user.update":
            self.setup_vote_delegation()
        else:
            self.setup_vote_delegation_temporary()

        response = self.request(action, request_data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"vote_delegated_$222_to_id": 2})
        user2 = self.get_model("user/2")
        self.assertCountEqual(user2["vote_delegations_$222_from_ids"], [1, 3])
        self.assert_model_exists("user/3", {"vote_delegated_$222_to_id": 2})
        user4 = self.get_model("user/4")
        self.assertIn(user4.get("vote_delegated_$222_to_id"), (None, []))

    def test_update_delegated_to_own_meeting_standard_user(self) -> None:
        setup_data = {"user/1": {"group_$_ids": ["222"], "group_$222_ids": [1]}}
        request_data = {"id": 1, "vote_delegated_$_to_id": {222: 2}}
        self.t_update_delegated_to_own_meeting("user.update", setup_data, request_data)

    def test_update_delegated_to_own_meeting_temporary_user(self) -> None:
        setup_data = {"user/1": {"meeting_id": 222}}
        request_data = {"id": 1, "vote_delegated_to_id": 2}
        self.t_update_delegated_to_own_meeting(
            "user.update_temporary", setup_data, request_data
        )

    def t_update_delegated_to_own_meeting(
        self, action: str, setup_data: Dict[str, Any], request_data: Dict[str, Any]
    ) -> None:
        """ user/1 delegates to user/2 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )
        self.set_models(setup_data)
        response = self.request(action, request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 222: ['user/2']",
            response.json["message"],
        )

    def test_update_delegated_to_other_meeting(self) -> None:
        """ user/1 delegates to user/2 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegated_$_to_id": {223: 2},
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 223: ['user/1']",
            response.json["message"],
        )

    def test_update_delegation_from_own_meeting_standard_user(self) -> None:
        setup_data = {"user/1": {"group_$_ids": ["222"], "group_$222_ids": [1]}}
        request_data = {"id": 1, "vote_delegations_$_from_ids": {222: [2]}}
        self.t_update_delegation_from_own_meeting(
            "user.update", setup_data, request_data
        )

    def test_update_delegation_from_own_meeting_temporary_user(self) -> None:
        setup_data = {"user/1": {"meeting_id": 222}}
        request_data = {"id": 1, "vote_delegations_from_ids": [2]}
        self.t_update_delegation_from_own_meeting(
            "user.update_temporary", setup_data, request_data
        )

    def t_update_delegation_from_own_meeting(
        self, action: str, setup_data: Dict[str, Any], request_data: Dict[str, Any]
    ) -> None:
        """ user/1 receive vote from user/2 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )
        self.set_models(setup_data)
        response = self.request(action, request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 222: ['user/2']",
            response.json["message"],
        )

    def test_update_delegation_from_other_meeting(self) -> None:
        """ user/1 receive vote from user/2 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegations_$_from_ids": {223: [2]},
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 223: ['user/1']",
            response.json["message"],
        )

    def test_update_delegation_from_other_meeting_with_guest_meeting_standard_user(
        self,
    ) -> None:
        """ user/1(222) receive vote from user/2(223) """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegations_$_from_ids": {223: [2]},
                "guest_meeting_ids": [223],
            },
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "group_$222_ids": [1],
                "group_$_ids": ["222"],
                "guest_meeting_ids": [223],
                "vote_delegations_$223_from_ids": [2],
                "vote_delegations_$_from_ids": ["223"],
            },
        )
        self.assert_model_exists(
            "user/2",
            {
                "group_$223_ids": [2],
                "group_$_ids": ["223"],
                "vote_delegated_$223_to_id": 1,
                "vote_delegated_$_to_id": ["223"],
            },
        )

    def test_update_delegation_from_other_meeting_with_guest_meeting_temporary_user(
        self,
    ) -> None:
        """ user/1(222) receive vote from user/2(223) """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/1": {
                    "meeting_id": 222,
                },
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )

        response = self.request(
            "user.update_temporary",
            {
                "id": 1,
                "vote_delegations_from_ids": [2],
                "guest_meeting_ids": [223],
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'guest_meeting_ids'} properties",
            response.json["message"],
        )
