from tests.system.action.base import BaseActionTestCase


class OptionUpdateActionTest(BaseActionTestCase):
    def test_update(self) -> None:
        self.set_models(
            {
                "meeting/110": {"name": "meeting_110"},
                "poll/65": {
                    "type": "analog",
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

    def test_update_Y(self) -> None:
        self.set_models(
            {
                "meeting/110": {"name": "meeting_110"},
                "poll/65": {
                    "type": "analog",
                    "pollmethod": "Y",
                    "meeting_id": 110,
                    "option_ids": [57],
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
            {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"},
        )
        self.assert_status_code(response, 200)
        option = self.get_model("option/57")
        assert option.get("yes") == "1.000000"
        assert option.get("no") == "0.000000"
        assert option.get("abstain") == "0.000000"

    def test_update_global_option(self) -> None:
        self.set_models(
            {
                "meeting/110": {"name": "meeting_110"},
                "poll/65": {
                    "type": "analog",
                    "pollmethod": "Y",
                    "meeting_id": 110,
                    "global_option_id": 57,
                    "global_yes": True,
                    "global_no": True,
                    "global_abstain": True,
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
