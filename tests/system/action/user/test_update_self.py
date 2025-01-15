from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserUpdateSelfActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models({"gender/1": {"name": "male"}})
        self.update_model(
            "user/1",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update_self",
            {
                "username": "username_Xcdfgee",
                "email": " email1@example.com   ",
                "pronoun": "Test",
                "gender_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert model.get("username") == "username_Xcdfgee"
        assert model.get("email") == "email1@example.com"
        assert model.get("pronoun") == "Test"
        assert model.get("gender_id") == 1
        self.assert_history_information("user/1", ["Personal data changed"])

    def test_username_already_given(self) -> None:
        self.create_model("user/222", {"username": "user"})
        response = self.request("user.update_self", {"username": "user"})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"] == "A user with the username user already exists."
        )

    def test_update_self_anonymus(self) -> None:
        response = self.request(
            "user.update_self",
            {"email": "user@openslides.org"},
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Anonymous is not allowed to execute user.update_self",
            response.json["message"],
        )

    def test_update_self_forbidden_username(self) -> None:
        self.update_model(
            "user/1",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update_self",
            {
                "username": "   ",
            },
        )
        self.assert_status_code(response, 400)
        model = self.get_model("user/1")
        assert model.get("username") == "username_srtgb123"
        assert "This username is forbidden." in response.json["message"]

    def test_update_self_strip_space(self) -> None:
        response = self.request(
            "user.update_self",
            {
                "username": " username test ",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "username": "username test",
            },
        )

    def test_update_broken_email(self) -> None:
        self.update_model(
            "user/1",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update_self",
            {
                "email": "broken@@",
            },
        )
        self.assert_status_code(response, 400)
        assert "email must be valid email." in response.json["message"]

    def test_update_delegation(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 1, "group_ids": []},
                "meeting/1": {
                    "meeting_user_ids": [11],
                },
            }
        )
        self.set_user_groups(1, [3])
        self.create_user("mandy", [3])
        self.create_user("andy", [3])
        self.create_user("sandy", [3])
        self.set_models(
            {
                "meeting_user/11": {"vote_delegations_from_ids": [13, 14]},
                "meeting_user/13": {"vote_delegated_to_id": 11},
                "meeting_user/14": {"vote_delegated_to_id": 11},
            }
        )
        response = self.request(
            "user.update_self",
            {
                "meeting_id": 1,
                "vote_delegated_to_id": 12,
                "vote_delegations_from_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/11",
            {"vote_delegated_to_id": 12, "vote_delegations_from_ids": []},
        )

    def test_update_foreign_delegation_error(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 1, "group_ids": []},
                "meeting/1": {
                    "meeting_user_ids": [11],
                },
            }
        )
        self.set_user_groups(1, [3])
        self.create_user("mandy", [3])
        self.create_user("andy", [3])
        self.create_user("sandy", [3])
        self.set_models(
            {
                "meeting_user/11": {"vote_delegations_from_ids": [13, 14]},
                "meeting_user/13": {"vote_delegated_to_id": 11},
                "meeting_user/14": {"vote_delegated_to_id": 11},
            }
        )
        response = self.request(
            "user.update_self",
            {
                "meeting_id": 1,
                "vote_delegations_from_ids": [12, 13, 14],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Can't add delegations from other people with user.update_self."
            in response.json["message"]
        )

    def test_update_reverse_delegation(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 1, "group_ids": []},
                "meeting/1": {
                    "meeting_user_ids": [11],
                },
            }
        )
        self.set_user_groups(1, [3])
        self.create_user("mandy", [3])
        self.set_models(
            {
                "meeting_user/11": {"vote_delegations_from_ids": [12]},
                "meeting_user/12": {"vote_delegated_to_id": 11},
            }
        )
        response = self.request(
            "user.update_self",
            {
                "meeting_id": 1,
                "vote_delegated_to_id": 12,
                "vote_delegations_from_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/11",
            {"vote_delegated_to_id": 12, "vote_delegations_from_ids": []},
        )

    def test_update_remove_delegation(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 1, "group_ids": []},
                "meeting/1": {
                    "meeting_user_ids": [11],
                },
            }
        )
        self.set_user_groups(1, [3])
        self.create_user("mandy", [3])
        self.create_user("andy", [3])
        self.set_models(
            {
                "meeting_user/11": {"vote_delegations_from_ids": [12, 13]},
                "meeting_user/12": {"vote_delegated_to_id": 11},
                "meeting_user/13": {"vote_delegated_to_id": 11},
            }
        )
        response = self.request(
            "user.update_self",
            {
                "meeting_id": 1,
                "vote_delegations_from_ids": [12],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/11",
            {"vote_delegations_from_ids": [12]},
        )

    def test_update_remove_delegation_2(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 1, "group_ids": []},
                "meeting/1": {
                    "meeting_user_ids": [11],
                },
            }
        )
        self.set_user_groups(1, [3])
        self.create_user("mandy", [3])
        self.set_models(
            {
                "meeting_user/11": {"vote_delegated_to_id": 12},
                "meeting_user/12": {"vote_delegations_from_ids": [11]},
            }
        )
        response = self.request(
            "user.update_self",
            {
                "meeting_id": 1,
                "vote_delegated_to_id": None,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/11",
            {"vote_delegated_to_id": None},
        )

    def test_update_delegation_without_meeting_id(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 1, "group_ids": []},
                "meeting/1": {
                    "meeting_user_ids": [11],
                },
            }
        )
        self.set_user_groups(1, [3])
        self.create_user("mandy", [3])
        response = self.request(
            "user.update_self",
            {"vote_delegated_to_id": 12},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Missing meeting_id in instance, because meeting related fields used",
            response.json["message"],
        )

    def test_update_delegation_wrong_meeting(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 1, "group_ids": []},
                "meeting/1": {
                    "meeting_user_ids": [11],
                },
            }
        )
        self.set_user_groups(1, [3])
        self.set_user_groups(1, [5])
        self.create_user("mandy", [3])
        response = self.request(
            "user.update_self",
            {"meeting_id": 4, "vote_delegated_to_id": 13},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 2's delegation id don't belong to meeting 4.",
            response.json["message"],
        )

    def test_update_with_meeting_id(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 1, "group_ids": []},
                "meeting/1": {
                    "meeting_user_ids": [11],
                },
            }
        )
        self.set_user_groups(1, [3])
        self.create_user("mandy", [3])
        response = self.request(
            "user.update_self",
            {
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/11", {"vote_delegated_to_id": None})

    def test_update_delegation_self(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 1, "group_ids": []},
                "meeting/1": {
                    "meeting_user_ids": [11],
                },
            }
        )
        self.set_user_groups(1, [3])
        self.create_user("mandy", [3])
        response = self.request(
            "user.update_self",
            {"meeting_id": 1, "vote_delegated_to_id": 11},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1 can't delegate the vote to himself.",
            response.json["message"],
        )

    def test_update_delegation_permission(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "meeting_user_ids": [11, 12],
                },
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "user/3": {"username": "username_srtgb124", "meeting_user_ids": [12]},
                "meeting_user/12": {"user_id": 3, "meeting_id": 1, "group_ids": [3]},
                "group/3": {"meeting_user_ids": [12]},
            },
            "user.update_self",
            {"meeting_id": 1, "vote_delegated_to_id": 12},
            Permissions.User.CAN_EDIT_OWN_DELEGATION,
        )

    def test_update_delegation_permission_denied(self) -> None:
        self.base_permission_test(
            {
                "meeting/1": {
                    "meeting_user_ids": [11, 12],
                },
                "user/1": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "user/3": {"username": "username_srtgb124", "meeting_user_ids": [12]},
                "meeting_user/12": {"user_id": 3, "meeting_id": 1, "group_ids": [3]},
                "group/3": {"meeting_user_ids": [12]},
            },
            "user.update_self",
            {"meeting_id": 1, "vote_delegated_to_id": 12},
            None,
        )
