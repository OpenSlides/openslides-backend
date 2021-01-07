from tests.system.action.base import BaseActionTestCase


class PollPublishActionTest(BaseActionTestCase):
    def test_publish_correct(self) -> None:
        self.create_model("poll/1", {"state": 3})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.publish",
                    "data": [{"id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        # check if the state has been changed to 4 (Published).
        poll = self.get_model("poll/1")
        assert poll.get("state") == 4

    def test_publish_wrong_state(self) -> None:
        self.create_model("poll/1", {"state": 1})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.publish",
                    "data": [{"id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == 1
        assert (
            "Cannot publish poll 1, because it is not in state 3 (Finished)."
            in response.data.decode()
        )
