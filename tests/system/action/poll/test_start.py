from tests.system.action.base import BaseActionTestCase


class PollStartActionTest(BaseActionTestCase):
    def test_start_correct(self) -> None:
        self.create_model("poll/1", {"state": 1})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.start",
                    "data": [{"id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        # check if the state has been changed to 2 (Started).
        poll = self.get_model("poll/1")
        assert poll.get("state") == 2

    def test_start_wrong_state(self) -> None:
        self.create_model("poll/1", {"state": 4})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.start",
                    "data": [{"id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == 4
        assert (
            "Cannot start poll 1, because it is not in state 1 (Created)."
            in response.data.decode()
        )
