from tests.system.action.base import BaseActionTestCase


class MeetingPollDefaultUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(17)
        self.set_models(
            {
                "meeting_poll_default/21": {"meeting_id": 17},
                "meeting/17": {"topic_poll_config_id": 21},
            }
        )

    def test_update_correctly(self) -> None:
        response = self.request(
            "meeting_poll_default.update",
            {"id": 21, "visibility": "named"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_poll_default/21", {"visibility": "named"})

    def test_update_erase_data(self) -> None:
        data = {
            "ballot_paper_selection": None,
            "ballot_paper_number": None,
            "sort_result_by_votes": None,
            "visibility": None,
            "allow_abstain": None,
            "allow_nota": None,
            "strike_out": None,
            "onehundred_percent_base": None,
            "group_ids": None,
            "display_chart": None,
        }
        response = self.request("meeting_poll_default.update", {"id": 21, **data})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_poll_default/21", data)

    def test_update_wrong_id(self) -> None:
        response = self.request(
            "meeting_poll_default.update", {"id": 200, "allow_abstain": False}
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("meeting_poll_default/21", {"allow_abstain": True})
        self.assertIn(
            "Model 'meeting_poll_default/200' does not exist.",
            response.json["message"],
        )

    def test_update_wrong_field(self) -> None:
        response = self.request(
            "meeting_poll_default.update",
            {
                "id": 21,
                "ballot_paper_number": 10,
                "wrong_id": "eleven",
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("meeting_poll_default/21", {"ballot_paper_number": 8})
        self.assertIn(
            "data must not contain {'wrong_id'} properties", response.json["message"]
        )
