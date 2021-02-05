from tests.system.action.base import BaseActionTestCase


class VoteDeleteTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("vote/111")
        response = self.request("vote.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("vote/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("vote/112")
        response = self.request("vote.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("vote/112")
