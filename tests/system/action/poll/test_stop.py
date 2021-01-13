from tests.system.action.base import BaseActionTestCase


class PollStopActionTest(BaseActionTestCase):
    def test_stop_correct(self) -> None:
        self.create_model("poll/1", {"state": "started"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.stop",
                    "data": [{"id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "finished"

    def test_start_wrong_state(self) -> None:
        self.create_model("poll/1", {"state": "published"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.stop",
                    "data": [{"id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "published"
        assert (
            "Cannot stop poll 1, because it is not in state started."
            in response.data.decode()
        )
