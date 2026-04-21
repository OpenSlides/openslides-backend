from decimal import Decimal

from tests.system.action.base import BaseActionTestCase


class VoteCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_meeting(111)
        self.set_models({"option/12": {"text": "blabalbal", "meeting_id": 111}})
        response = self.request(
            "vote.create",
            {
                "value": "Y",
                "weight": "1.000000",
                "option_id": 12,
                "user_token": "aaaabbbbccccdddd",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "vote/1",
            {
                "value": "Y",
                "meeting_id": 111,
                "weight": Decimal("1.000000"),
                "option_id": 12,
                "user_token": "aaaabbbbccccdddd",
            },
        )
        self.assert_model_exists("option/12", {"vote_ids": [1]})
