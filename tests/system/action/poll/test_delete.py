from tests.system.action.base import BaseActionTestCase


class PollDeleteTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("poll/111", {})
        response = self.client.post(
            "/",
            json=[{"action": "poll.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("poll/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("poll/112", {})
        response = self.client.post(
            "/",
            json=[{"action": "poll.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("poll/112")

    def test_delete_correct_cascading(self) -> None:
        self.create_model(
            "poll/111",
            {
                "option_ids": [42],
            },
        )
        self.create_model(
            "option/42",
            {"poll_id": 111},
        )
        response = self.client.post(
            "/",
            json=[{"action": "poll.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("poll/111")
        self.assert_model_deleted("option/42")
