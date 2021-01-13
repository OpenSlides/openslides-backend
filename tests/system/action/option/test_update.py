from tests.system.action.base import BaseActionTestCase


class OptionUpdateActionTest(BaseActionTestCase):
    def test_update(self) -> None:
        self.create_model("meeting/110", {"name": "meeting_110"})
        self.create_model(
            "option/57",
            {
                "yes": "0.000000",
                "no": "0.000000",
                "abstain": "0.000000",
                "meeting_id": 110,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "option.update",
                    "data": [
                        {"id": 57, "Y": "1.000000", "N": "2.000000", "A": "3.000000"}
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        option = self.get_model("option/57")
        assert option.get("yes") == "1.000000"
        assert option.get("no") == "2.000000"
        assert option.get("abstain") == "3.000000"
