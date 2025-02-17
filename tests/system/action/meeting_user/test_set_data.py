import pytest

from tests.system.action.base import BaseActionTestCase


class MeetingUserSetData(BaseActionTestCase):
    def test_set_data_with_meeting_user(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                    "structure_level_ids": [31],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "structure_level/31": {"meeting_id": 10},
            }
        )
        test_dict = {
            "meeting_id": 10,
            "user_id": 1,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/5", test_dict)

    def test_set_data_with_meeting_user_and_id(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                    "structure_level_ids": [31],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "structure_level/31": {"meeting_id": 10},
            }
        )
        test_dict = {
            "id": 5,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/5", {"meeting_id": 10, "user_id": 1, **test_dict}
        )

    def test_set_data_with_meeting_user_and_wrong_meeting_id(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
            }
        )
        test_dict = {
            "id": 5,
            "meeting_id": 12,
            "comment": "test bla",
        }
        with pytest.raises(AssertionError, match="Not permitted to change meeting_id."):
            self.request("meeting_user.set_data", test_dict)

    def test_set_data_with_meeting_user_and_wrong_user_id(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
            }
        )
        test_dict = {
            "id": 5,
            "user_id": 3,
            "comment": "test bla",
        }
        with pytest.raises(AssertionError, match="Not permitted to change user_id."):
            self.request("meeting_user.set_data", test_dict)

    def test_set_data_without_meeting_user(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [],
                    "structure_level_ids": [31],
                },
                "structure_level/31": {"meeting_id": 10},
            }
        )
        test_dict = {
            "meeting_id": 10,
            "user_id": 1,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", test_dict)

    def test_set_data_missing_identifiers(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
            }
        )
        test_dict = {
            "comment": "test bla",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 400)
        assert (
            "Identifier for meeting_user instance required, but neither id nor meeting_id/user_id is given."
            == response.json["message"]
        )

    def test_prevent_zero_vote_weight(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {
                    "user_id": 1,
                    "meeting_id": 10,
                    "vote_weight": "1.000000",
                },
            }
        )
        response = self.request("meeting_user.set_data", {"vote_weight": "0.000000"})
        self.assert_status_code(response, 400)
        self.assert_model_exists("meeting_user/5", {"vote_weight": "1.000000"})

    def test_set_data_anonymous_group_id(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4]},
                "group/4": {"anonymous_group_for_meeting_id": 1},
            }
        )
        self.create_user("dummy", [1])
        response = self.request(
            "meeting_user.set_data",
            {
                "id": 1,
                "group_ids": [4],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot add explicit users to a meetings anonymous group",
            response.json["message"],
        )

    def test_set_data_anonymous_group_id_2(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4]},
                "group/4": {"anonymous_group_for_meeting_id": 1},
            }
        )
        user_id = self.create_user("dummy")
        response = self.request(
            "meeting_user.set_data",
            {
                "user_id": user_id,
                "meeting_id": 1,
                "group_ids": [1, 4],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot add explicit users to a meetings anonymous group",
            response.json["message"],
        )

    def test_set_data_delegate_vote(self) -> None:
        self.create_meeting()
        bob_id = self.create_user("bob", [3])
        alice_id = self.create_user("alice", [3])
        response = self.request(
            "meeting_user.set_data",
            {"id": alice_id - 1, "vote_delegated_to_id": bob_id - 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            f"meeting_user/{alice_id - 1}",
            {"user_id": alice_id, "vote_delegated_to_id": bob_id - 1},
        )
        self.assert_model_exists(
            f"meeting_user/{bob_id - 1}",
            {"user_id": bob_id, "vote_delegations_from_ids": [alice_id - 1]},
        )
        self.assert_history_information(
            f"user/{bob_id}",
            [
                "Proxy voting rights received in meeting {}",
                "meeting/1",
            ],
        )
        self.assert_history_information(
            f"user/{alice_id}",
            ["Vote delegated to {} in meeting {}", f"user/{bob_id}", "meeting/1"],
        )

    def test_set_data_receive_delegated_vote(self) -> None:
        self.create_meeting()
        bob_id = self.create_user("bob", [3])
        alice_id = self.create_user("alice", [3])
        response = self.request(
            "meeting_user.set_data",
            {"id": alice_id - 1, "vote_delegations_from_ids": [bob_id - 1]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            f"meeting_user/{alice_id - 1}",
            {"user_id": alice_id, "vote_delegations_from_ids": [bob_id - 1]},
        )
        self.assert_history_information(
            f"user/{bob_id}",
            ["Vote delegated to {} in meeting {}", f"user/{alice_id}", "meeting/1"],
        )
        self.assert_history_information(
            f"user/{alice_id}",
            [
                "Proxy voting rights received in meeting {}",
                "meeting/1",
            ],
        )

    def test_set_data_re_delegate_vote(self) -> None:
        self.create_meeting()
        bob_id = self.create_user("bob", [3])
        alice_id = self.create_user("alice", [3])
        tom_id = self.create_user("tom", [3])
        self.set_models(
            {
                f"meeting_user/{alice_id-1}": {"vote_delegated_to_id": tom_id - 1},
                f"meeting_user/{tom_id-1}": {
                    "vote_delegations_from_ids": [alice_id - 1]
                },
            }
        )
        response = self.request(
            "meeting_user.set_data",
            {"id": alice_id - 1, "vote_delegated_to_id": bob_id - 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            f"meeting_user/{alice_id - 1}",
            {"user_id": alice_id, "vote_delegated_to_id": bob_id - 1},
        )
        self.assert_history_information(
            f"user/{bob_id}",
            [
                "Proxy voting rights received in meeting {}",
                "meeting/1",
            ],
        )
        self.assert_history_information(
            f"user/{alice_id}",
            ["Vote delegated to {} in meeting {}", f"user/{bob_id}", "meeting/1"],
        )
        self.assert_history_information(
            f"user/{tom_id}",
            ["Proxy voting rights removed in meeting {}", "meeting/1"],
        )

    def test_set_data_re_delegate_received_votes(self) -> None:
        self.create_meeting()
        bob_id = self.create_user("bob", [3])
        alice_id = self.create_user("alice", [3])
        tom_id = self.create_user("tom", [3])
        self.set_models(
            {
                f"meeting_user/{alice_id-1}": {
                    "vote_delegations_from_ids": [tom_id - 1]
                },
                f"meeting_user/{tom_id-1}": {"vote_delegated_to_id": alice_id - 1},
            }
        )
        response = self.request(
            "meeting_user.set_data",
            {"id": alice_id - 1, "vote_delegations_from_ids": [bob_id - 1]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            f"meeting_user/{alice_id - 1}",
            {"user_id": alice_id, "vote_delegations_from_ids": [bob_id - 1]},
        )
        self.assert_history_information(
            f"user/{bob_id}",
            ["Vote delegated to {} in meeting {}", f"user/{alice_id}", "meeting/1"],
        )
        self.assert_history_information(
            f"user/{alice_id}",
            [
                "Proxy voting rights received in meeting {}",
                "meeting/1",
                "Proxy voting rights removed in meeting {}",
                "meeting/1",
            ],
        )
        self.assert_history_information(
            f"user/{tom_id}",
            ["Vote delegation canceled in meeting {}", "meeting/1"],
        )
