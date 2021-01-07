from tests.system.action.base import BaseActionTestCase


class OptionDeleteTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("option/111", {})
        response = self.client.post(
            "/",
            json=[{"action": "option.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("option/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("option/112", {})
        response = self.client.post(
            "/",
            json=[{"action": "option.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("option/112")

    def test_delete_correct_cascading(self) -> None:
        self.create_model(
            "option/111",
            {
                "vote_ids": [42],
            },
        )
        self.create_model(
            "vote/42",
            {"option_id": 111},
        )
        response = self.client.post(
            "/",
            json=[{"action": "option.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("option/111")
        self.assert_model_deleted("vote/42")
