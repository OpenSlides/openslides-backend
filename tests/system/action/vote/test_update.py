from tests.system.action.base import BaseActionTestCase


class VoteUpdateActionTest(BaseActionTestCase):
    def test_update(self) -> None:
        self.set_models(
            {
                "meeting/111": {"name": "meeting_Xcdfgee"},
                "option/12": {"text": "blabalbal", "meeting_id": 111},
                "vote/1": {
                    "value": "Y",
                    "meeting_id": 111,
                    "weight": "1.000000",
                    "option_id": 12,
                },
            }
        )

        response = self.request(
            "vote.update",
            {
                "id": 1,
                "weight": "1.500000",
            },
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "Y"
        assert vote.get("meeting_id") == 111
        assert vote.get("weight") == "1.500000"
