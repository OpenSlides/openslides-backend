from decimal import Decimal

from .base_poll_test import BasePollTestCase


class PollSetState(BasePollTestCase):
    def test_set_state(self) -> None:
        self.create_meeting(110)
        self.create_assignment(1, 110)
        self.set_models(
            {
                "poll/65": {
                    "title": "Title 65",
                    "type": "analog",
                    "state": "created",
                    "pollmethod": "YNA",
                    "meeting_id": 110,
                    "content_object_id": "assignment/1",
                },
                "option/57": {
                    "yes": Decimal("0.000000"),
                    "no": Decimal("0.000000"),
                    "abstain": Decimal("0.000000"),
                    "meeting_id": 110,
                    "poll_id": 65,
                },
            }
        )
        response = self.request("poll.set_state", {"id": 65, "state": "finished"})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/65")
        assert poll.get("state") == "finished"
