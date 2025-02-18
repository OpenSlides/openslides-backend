from typing import Any

from tests.system.action.base import BaseActionTestCase


class UserActionDelegationHistoryTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.alice_id = self.create_user("alice", [3])
        self.bob_id = self.create_user("bob", [3])
        self.tom_id = self.create_user("tom", [3])
        self.next_user_id = self.tom_id + 1

    def make_request(self, instance: dict[str, Any], id_: int | None = None) -> None:
        if "meeting_id" not in instance:
            instance["meeting_id"] = 1
        if id_ is not None:
            response = self.request("user.update", {"id": id_, **instance})
        else:
            response = self.request("user.create", instance)
        self.assert_status_code(response, 200)

    def assert_alice_delegated_to_bob(self) -> None:
        self.assert_history_information(
            f"user/{self.bob_id}",
            [
                "Proxy voting rights received in meeting {}",
                "meeting/1",
            ],
        )
        self.assert_history_information(
            f"user/{self.alice_id}",
            ["Vote delegated to {} in meeting {}", f"user/{self.bob_id}", "meeting/1"],
        )

    def test_update_delegate_vote(self) -> None:
        self.make_request({"vote_delegated_to_id": self.bob_id - 1}, self.alice_id)
        self.assert_alice_delegated_to_bob()

    def test_update_receive_delegated_vote(self) -> None:
        self.make_request(
            {"vote_delegations_from_ids": [self.alice_id - 1]}, self.bob_id
        )
        self.assert_alice_delegated_to_bob()

    def setup_delegation(self) -> None:
        self.set_models(
            {
                f"meeting_user/{self.alice_id-1}": {
                    "vote_delegated_to_id": self.tom_id - 1
                },
                f"meeting_user/{self.tom_id-1}": {
                    "vote_delegations_from_ids": [self.alice_id - 1]
                },
            }
        )

    def assert_alice_redelegated_to_bob(self) -> None:
        self.assert_history_information(
            f"user/{self.bob_id}",
            [
                "Proxy voting rights received in meeting {}",
                "meeting/1",
            ],
        )
        self.assert_history_information(
            f"user/{self.alice_id}",
            ["Vote delegated to {} in meeting {}", f"user/{self.bob_id}", "meeting/1"],
        )
        self.assert_history_information(
            f"user/{self.tom_id}",
            ["Proxy voting rights removed in meeting {}", "meeting/1"],
        )

    def test_update_re_delegate_vote(self) -> None:
        self.setup_delegation()
        self.make_request({"vote_delegated_to_id": self.bob_id - 1}, self.alice_id)
        self.assert_alice_redelegated_to_bob()

    def test_update_re_delegate_vote_reverse(self) -> None:
        self.setup_delegation()
        self.make_request(
            {"vote_delegations_from_ids": [self.alice_id - 1]}, self.bob_id
        )
        self.assert_alice_redelegated_to_bob()

    def test_update_re_delegate_received_votes(self) -> None:
        self.setup_delegation()
        self.make_request({"vote_delegations_from_ids": [self.bob_id - 1]}, self.tom_id)
        self.assert_history_information(
            f"user/{self.bob_id}",
            [
                "Vote delegated to {} in meeting {}",
                f"user/{self.tom_id}",
                "meeting/1",
            ],
        )
        self.assert_history_information(
            f"user/{self.tom_id}",
            [
                "Proxy voting rights removed in meeting {}",
                "meeting/1",
                "Proxy voting rights received in meeting {}",
                "meeting/1",
            ],
        )
        self.assert_history_information(
            f"user/{self.alice_id}",
            ["Vote delegation canceled in meeting {}", "meeting/1"],
        )

    def test_update_remove_received_delegation_and_delegate(self) -> None:
        self.setup_delegation()
        self.make_request(
            {"vote_delegations_from_ids": [], "vote_delegated_to_id": self.bob_id - 1},
            self.tom_id,
        )
        self.assert_history_information(
            f"user/{self.bob_id}",
            [
                "Proxy voting rights received in meeting {}",
                "meeting/1",
            ],
        )
        self.assert_history_information(
            f"user/{self.tom_id}",
            [
                "Vote delegated to {} in meeting {}",
                f"user/{self.bob_id}",
                "meeting/1",
                "Proxy voting rights removed in meeting {}",
                "meeting/1",
            ],
        )
        self.assert_history_information(
            f"user/{self.alice_id}",
            ["Vote delegation canceled in meeting {}", "meeting/1"],
        )

    def test_update_remove_delegation_and_receive_new_one(self) -> None:
        self.setup_delegation()
        self.make_request(
            {
                "vote_delegations_from_ids": [self.bob_id - 1],
                "vote_delegated_to_id": None,
            },
            self.alice_id,
        )
        self.assert_history_information(
            f"user/{self.bob_id}",
            ["Vote delegated to {} in meeting {}", "user/3", "meeting/1"],
        )
        self.assert_history_information(
            f"user/{self.tom_id}",
            ["Proxy voting rights removed in meeting {}", "meeting/1"],
        )
        self.assert_history_information(
            f"user/{self.alice_id}",
            [
                "Vote delegation canceled in meeting {}",
                "meeting/1",
                "Proxy voting rights received in meeting {}",
                "meeting/1",
            ],
        )

    def base_update_same_delegation(self, set_to: bool) -> None:
        data: dict[str, dict[str, Any]] = {
            f"meeting_user/{self.alice_id-1}": {
                "vote_delegations_from_ids": [self.bob_id - 1]
            },
            f"meeting_user/{self.bob_id-1}": {
                "vote_delegated_to_id": self.alice_id - 1
            },
        }
        self.set_models(data)
        primary = self.bob_id if set_to else self.alice_id
        self.make_request(data[f"meeting_user/{primary - 1}"], primary)
        self.assert_history_information(
            f"user/{self.bob_id}",
            None,
        )
        self.assert_history_information(
            f"user/{self.alice_id}",
            None,
        )

    def test_update_delegate_from_same(self) -> None:
        self.base_update_same_delegation(False)

    def test_update_delegate_to_same(self) -> None:
        self.base_update_same_delegation(True)
