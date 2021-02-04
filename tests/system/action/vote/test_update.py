from tests.system.action.base import BaseActionTestCase


class VoteUpdateActionTest(BaseActionTestCase):
    def test_update(self) -> None:
        self.create_model("meeting/111", {"name": "meeting_Xcdfgee"})
        self.create_model("option/12", {"text": "blabalbal", "meeting_id": 111})
        self.create_model(
            "vote/1",
            {
                "value": "Y",
                "meeting_id": 111,
                "weight": "1.000000",
                "option_id": 12,
            },
        )

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "vote.update",
                    "data": [
                        {
                            "id": 1,
                            "weight": "1.500000",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "Y"
        assert vote.get("meeting_id") == 111
        assert vote.get("weight") == "1.500000"
