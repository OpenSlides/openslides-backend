from decimal import Decimal

from tests.system.action.base import BaseActionTestCase


class VoteUpdateActionTest(BaseActionTestCase):
    def test_update(self) -> None:
        self.create_meeting(111)
        self.set_models(
            {
                "option/12": {"text": "blabalbal", "meeting_id": 111},
                "vote/1": {
                    "value": "Y",
                    "meeting_id": 111,
                    "weight": "1.000000",
                    "option_id": 12,
                    "user_token": "aaaabbbbccccdddd",
                },
            }
        )

        response = self.request("vote.update", {"id": 1, "weight": "1.500000"})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "vote/1", {"value": "Y", "meeting_id": 111, "weight": Decimal("1.500000")}
        )
