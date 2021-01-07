from tests.system.action.base import BaseActionTestCase


class PollStopActionTest(BaseActionTestCase):
    def test_stop_correct(self) -> None:
        self.create_model("poll/1", {"state": 2})
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
        # check if the state has been changed to 3 (Finished).
        poll = self.get_model("poll/1")
        assert poll.get("state") == 3

    def test_start_wrong_state(self) -> None:
        self.create_model("poll/1", {"state": 4})
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
        assert poll.get("state") == 4
        assert (
            "Cannot stop poll 1, because it is not in state 2 (Started)."
            in response.data.decode()
        )
