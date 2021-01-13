from tests.system.action.base import BaseActionTestCase


class PollPublishActionTest(BaseActionTestCase):
    def test_publish_correct(self) -> None:
        self.create_model("poll/1", {"state": "finished"})
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
        poll = self.get_model("poll/1")
        assert poll.get("state") == "published"

    def test_publish_wrong_state(self) -> None:
        self.create_model("poll/1", {"state": "created"})
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
        assert poll.get("state") == "created"
        assert (
            "Cannot publish poll 1, because it is not in state finished."
            in response.data.decode()
        )
