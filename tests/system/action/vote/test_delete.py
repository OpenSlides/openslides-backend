from tests.system.action.base import BaseActionTestCase


class VoteDeleteTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "option/12": {"text": "blabalbal", "meeting_id": 1},
                "vote/111": {
                    "meeting_id": 1,
                    "option_id": 12,
                    "user_token": "aaaabbbbccccdddd",
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("vote.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("vote/111")

    def test_delete_wrong_id(self) -> None:
        response = self.request("vote.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assert_model_exists("vote/111")
