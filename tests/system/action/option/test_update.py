from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class OptionUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "poll/65": {
                "type": "analog",
                "state": "created",
                "pollmethod": "YNA",
                "meeting_id": 1,
                "option_ids": [57],
            },
            "option/57": {
                "yes": "0.000000",
                "no": "0.000000",
                "abstain": "0.000000",
                "meeting_id": 1,
                "poll_id": 65,
                "vote_ids": [22],
            },
            "vote/22": {
                "value": "Y",
                "weight": "0.000000",
                "meeting_id": 1,
                "option_id": 57,
            },
        }

    def test_update(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "meeting_110",
                    "is_active_in_organization_id": 1,
                },
                "poll/65": {
                    "type": "analog",
                    "state": "created",
                    "pollmethod": "YNA",
                    "meeting_id": 110,
                    "option_ids": [57],
                },
                "option/57": {
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                    "meeting_id": 110,
                    "poll_id": 65,
                    "vote_ids": [22],
                },
                "vote/22": {
                    "value": "Y",
                    "weight": "0.000000",
                    "meeting_id": 110,
                    "option_id": 57,
                },
            }
        )
        response = self.request(
            "option.update",
            {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"},
        )
        self.assert_status_code(response, 200)
        option = self.get_model("option/57")
        assert option.get("yes") == "1.000000"
        assert option.get("no") == "2.000000"
        assert option.get("abstain") == "3.000000"
        assert option.get("vote_ids") == [22, 23, 24]
        vote_22 = self.get_model("vote/22")
        assert vote_22.get("value") == "Y"
        assert vote_22.get("weight") == "1.000000"
        vote_23 = self.get_model("vote/23")
        assert vote_23.get("option_id") == 57
        assert vote_23.get("value") == "N"
        assert vote_23.get("weight") == "2.000000"
        vote_24 = self.get_model("vote/24")
        assert vote_24.get("option_id") == 57
        assert vote_24.get("value") == "A"
        assert vote_24.get("weight") == "3.000000"
        poll = self.get_model("poll/65")
        assert poll.get("state") == "finished"

    def test_update_Y(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "meeting_110",
                    "is_active_in_organization_id": 1,
                },
                "poll/65": {
                    "type": "analog",
                    "pollmethod": "Y",
                    "meeting_id": 110,
                    "option_ids": [57],
                    "state": "created",
                },
                "option/57": {
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                    "meeting_id": 110,
                    "poll_id": 65,
                },
            }
        )
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
        option = self.get_model("option/57")
        assert option.get("yes") == "1.000000"
        assert option.get("no") == "0.000000"
        assert option.get("abstain") == "0.000000"
        poll = self.get_model("poll/65")
        assert poll.get("state") == "published"

    def test_update_global_option(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "meeting_110",
                    "is_active_in_organization_id": 1,
                },
                "poll/65": {
                    "type": "analog",
                    "pollmethod": "Y",
                    "meeting_id": 110,
                    "global_option_id": 57,
                    "global_yes": True,
                    "global_no": True,
                    "global_abstain": True,
                    "state": "created",
                },
                "option/57": {
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                    "meeting_id": 110,
                    "used_as_global_option_in_poll_id": 65,
                },
            }
        )
        response = self.request(
            "option.update",
            {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"},
        )
        self.assert_status_code(response, 200)
        option = self.get_model("option/57")
        assert option.get("yes") == "1.000000"
        assert option.get("no") == "2.000000"
        assert option.get("abstain") == "3.000000"

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "option.update",
            {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "option.update",
            {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_update_together_with_poll(self) -> None:
        self.set_models(
            {
                "meeting/110": {"is_active_in_organization_id": 1},
                "poll/6": {
                    "type": "analog",
                    "state": "created",
                    "pollmethod": "YN",
                    "meeting_id": 110,
                    "option_ids": [14, 15],
                },
                "option/14": {
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                    "meeting_id": 110,
                    "poll_id": 6,
                },
                "option/15": {
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                    "meeting_id": 110,
                    "poll_id": 6,
                },
            }
        )
        response = self.request_json(
            [
                {
                    "action": "poll.update",
                    "data": [
                        {
                            "id": 6,
                            "onehundred_percent_base": "valid",
                            "pollmethod": "YNA",
                            "title": "Ballot",
                        }
                    ],
                },
                {
                    "action": "option.update",
                    "data": [
                        {"id": 14, "Y": "1.000000", "A": "3.000000", "N": "2.000000"},
                        {"id": 15, "Y": "4.000000", "N": "-1.000000"},
                    ],
                },
            ]
        )
        self.assert_status_code(response, 200)

    def test_update_together_with_poll_2(self) -> None:
        self.set_models(
            {
                "meeting/110": {"is_active_in_organization_id": 1},
                "poll/13": {
                    "type": "analog",
                    "state": "created",
                    "pollmethod": "YN",
                    "meeting_id": 110,
                    "option_ids": [30],
                },
                "option/30": {
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                    "meeting_id": 110,
                    "poll_id": 13,
                },
            }
        )
        response = self.request_json(
            [
                {
                    "action": "poll.update",
                    "data": [
                        {
                            "id": 13,
                            "max_votes_amount": 1,
                            "max_votes_per_person": 1,
                            "min_votes_amount": 1,
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
                        {"id": 30, "Y": "10.000000", "A": "10.000000", "N": "10.000000"}
                    ],
                },
            ]
        )
        self.assert_status_code(response, 200)
