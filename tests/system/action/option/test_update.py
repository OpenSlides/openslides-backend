from decimal import Decimal
from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class OptionUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.vote_models: dict[str, dict[str, Any]] = {
            "option/57": {
                "vote_ids": [22],
            },
            "vote/22": {
                "value": "Y",
                "user_token": "imnotapropertoken",
                "weight": "0.000000",
                "meeting_id": 1,
                "option_id": 57,
            },
        }
        self.create_meeting()
        self.set_models(
            {
                "topic/1": {
                    "title": "to pic",
                    "meeting_id": 1,
                },
                "agenda_item/1": {"content_object_id": "topic/1", "meeting_id": 1},
                "list_of_speakers/23": {
                    "content_object_id": "topic/1",
                    "meeting_id": 1,
                },
                "poll/65": {
                    "title": "pool",
                    "content_object_id": "topic/1",
                    "type": "analog",
                    "state": "created",
                    "pollmethod": "YNA",
                    "max_votes_amount": 1,
                    "max_votes_per_option": 1,
                    "min_votes_amount": 1,
                    "meeting_id": 1,
                    "option_ids": [57],
                },
                "option/57": {
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                    "meeting_id": 1,
                    "poll_id": 65,
                },
            }
        )

    def test_update(self) -> None:
        self.set_models(self.vote_models)
        response = self.request(
            "option.update",
            {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "option/57",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("2.000000"),
                "abstain": Decimal("3.000000"),
                "vote_ids": [22, 23, 24],
            },
        )
        self.assert_model_exists(
            "vote/22", {"option_id": 57, "value": "Y", "weight": Decimal("1.000000")}
        )
        self.assert_model_exists(
            "vote/23", {"option_id": 57, "value": "N", "weight": Decimal("2.000000")}
        )
        self.assert_model_exists(
            "vote/24", {"option_id": 57, "value": "A", "weight": Decimal("3.000000")}
        )
        poll = self.get_model("poll/65")
        assert poll.get("state") == "finished"

    def test_update_Y(self) -> None:
        response = self.request(
            "option.update",
            {
                "id": 57,
                "Y": "1.000000",
                "N": "2.000000",
                "A": "3.000000",
                "publish_immediately": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "option/57",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("2.000000"),
                "abstain": Decimal("3.000000"),
                "publish_immediately": None,
            },
        )
        poll = self.get_model("poll/65")
        assert poll.get("state") == "published"

    def test_update_default_values(self) -> None:
        self.set_models(
            {
                "poll/65": {
                    "pollmethod": "YN",
                },
                "option/57": {
                    "abstain": None,
                },
            }
        )
        response = self.request(
            "option.update",
            {
                "id": 57,
                "Y": "1.000000",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "option/57",
            {"yes": Decimal("1.000000"), "no": Decimal("-2.000000"), "abstain": None},
        )

    def test_update_invalid_keys(self) -> None:
        self.set_models(
            {
                "poll/65": {
                    "pollmethod": "YN",
                },
            }
        )
        response = self.request(
            "option.update",
            {
                "id": 57,
                "A": "0.000000",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Pollmethod YN does not support abstain votes" in response.json["message"]
        )

    def test_update_global_option(self) -> None:
        self.set_models(
            {
                "poll/65": {
                    "pollmethod": "Y",
                    "global_option_id": 57,
                    "global_yes": True,
                    "global_no": True,
                    "global_abstain": True,
                },
                "option/57": {"used_as_global_option_in_poll_id": 65},
            }
        )
        response = self.request(
            "option.update",
            {"id": 57, "Y": "1.000000", "N": "2.000000"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "option/57",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("2.000000"),
                "abstain": Decimal("-2.000000"),
            },
        )

    def test_update_global_option_invalid(self) -> None:
        self.set_models({"option/57": {"used_as_global_option_in_poll_id": 65}})
        response = self.request(
            "option.update",
            {"id": 57, "Y": "1.000000"},
        )
        self.assert_status_code(response, 400)
        assert (
            "Global yes votes are not allowed for this poll" in response.json["message"]
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.vote_models,
            "option.update",
            {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.vote_models,
            "option.update",
            {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.vote_models,
            "option.update",
            {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"},
        )

    def test_update_together_with_poll(self) -> None:
        self.set_models(
            {
                "poll/65": {
                    "pollmethod": "YN",
                    "option_ids": [57, 58],
                },
                "option/58": {
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                    "meeting_id": 1,
                    "poll_id": 65,
                },
            }
        )
        response = self.request_json(
            [
                {
                    "action": "poll.update",
                    "data": [
                        {
                            "id": 65,
                            "onehundred_percent_base": "valid",
                            "pollmethod": "YNA",
                            "title": "Ballot",
                        }
                    ],
                },
                {
                    "action": "option.update",
                    "data": [
                        {"id": 57, "Y": "1.000000", "A": "3.000000", "N": "2.000000"},
                        {"id": 58, "Y": "4.000000", "N": "-1.000000"},
                    ],
                },
            ]
        )
        self.assert_status_code(response, 200)

    def test_update_together_with_poll_2(self) -> None:
        response = self.request_json(
            [
                {
                    "action": "poll.update",
                    "data": [
                        {
                            "id": 65,
                            "onehundred_percent_base": "YNA",
                            "pollmethod": "YNA",
                            "title": "Abstimmung",
                            "votescast": "10.000000",
                            "votesinvalid": "10.000000",
                            "votesvalid": "10.000000",
                        }
                    ],
                },
                {
                    "action": "option.update",
                    "data": [
                        {"id": 57, "Y": "10.000000", "A": "10.000000", "N": "10.000000"}
                    ],
                },
            ]
        )
        self.assert_status_code(response, 200)
