from tests.system.action.base import BaseActionTestCase


class OptionDeleteTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "option/111": {"meeting_id": 1, "content_object_id": "motion/1"},
                "motion/1": {
                    "sequential_number": 1,
                    "title": "moshen",
                    "state_id": 1,
                    "meeting_id": 1,
                },
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("option.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("option/111")
        self.assert_model_exists("motion/1")

    def test_delete_wrong_id(self) -> None:
        response = self.request("option.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assert_model_exists("option/111")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "option/112": {
                    "meeting_id": 1,
                    "content_object_id": "poll_candidate_list/2",
                },
                "vote/42": {"user_token": "imnotapropertoken", "option_id": 112, "meeting_id": 1},
                "poll_candidate_list/2": {"option_id": 112, "meeting_id": 1},
            }
        )
        response = self.request("option.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("option/112")
        self.assert_model_not_exists("vote/42")
