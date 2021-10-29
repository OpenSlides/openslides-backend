from tests.system.action.base import BaseActionTestCase


class OptionDeleteTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "option/111": {"meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )

    def test_delete_correct(self) -> None:
        response = self.request("option.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("option/111")

    def test_delete_wrong_id(self) -> None:
        response = self.request("option.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assert_model_exists("option/111")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "option/112": {
                    "vote_ids": [42],
                    "meeting_id": 1,
                },
                "vote/42": {"option_id": 112, "meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("option.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("option/112")
        self.assert_model_deleted("vote/42")
