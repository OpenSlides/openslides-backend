from .base_poll_test import BasePollTestCase


class PollSetState(BasePollTestCase):
    def test_set_state(self) -> None:
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
                    "vote_ids": [],
                },
            }
        )
        response = self.request("poll.set_state", {"id": 65, "state": "finished"})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/65")
        assert poll.get("state") == "finished"
