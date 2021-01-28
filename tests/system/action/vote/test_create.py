from tests.system.action.base import BaseActionTestCase


class VoteCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/111", {"name": "meeting_Xcdfgee"})
        self.create_model("option/12", {"text": "blabalbal", "meeting_id": 111})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "vote.create",
                    "data": [
                        {
                            "value": "Y",
                            "meeting_id": 111,
                            "weight": "1.000000",
                            "option_id": 12,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "Y"
        assert vote.get("meeting_id") == 111
        assert vote.get("weight") == "1.000000"
        assert vote.get("option_id") == 12
        option = self.get_model("option/12")
        assert option.get("vote_ids") == [1]
