from tests.system.action.base import BaseActionTestCase


class PollStopActionTest(BaseActionTestCase):
    def test_stop_correct(self) -> None:
        self.set_models(
            {
                "poll/1": {"state": "started", "meeting_id": 1},
                "meeting/1": {"poll_couple_countdown": True, "poll_countdown_id": 1},
                "projector_countdown/1": {
                    "running": True,
                    "default_time": 60,
                    "countdown_time": 30.0,
                },
            }
        )
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "finished"
        countdown = self.get_model("projector_countdown/1")
        assert countdown.get("running") is False
        assert countdown.get("countdown_time") == 60

    def test_stop_wrong_state(self) -> None:
        self.create_model("poll/1", {"state": "published"})
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "published"
        assert (
            "Cannot stop poll 1, because it is not in state started."
            in response.json["message"]
        )
