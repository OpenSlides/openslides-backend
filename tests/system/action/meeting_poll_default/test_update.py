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
            "sort_result_by_votes": None,
            "visibility": None,
            "onehundred_percent_base": None,
            "group_ids": None,
            "enable_cumulative_voting": None,
            "allow_live_voting": None,
            "default_live_voting_enabled": None,
            "enable_max_options_limit": None,
            "enable_max_yes_votes": None,
            "default_method": None,
            "default_required_majority": None,
        }
        response = self.request("meeting_poll_default.update", {"id": 21, **data})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_poll_default/21", data)

    def test_update_wrong_id(self) -> None:
        response = self.request(
            "meeting_poll_default.update", {"id": 200, "enable_cumulative_voting": True}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model 'meeting_poll_default/200' does not exist.",
            response.json["message"],
        )

    def test_update_wrong_field(self) -> None:
        response = self.request(
            "meeting_poll_default.update",
            {
                "id": 21,
                "default_live_voting_enabled": True,
                "wrong_id": "eleven",
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists(
            "meeting_poll_default/21", {"default_live_voting_enabled": False}
        )
        self.assertIn(
            "data must not contain {'wrong_id'} properties", response.json["message"]
        )

    def test_update_group_ids_not_in_meeting(self) -> None:
        self.create_meeting()
        response = self.request(
            "meeting_poll_default.update",
            {
                "id": 21,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The following models do not belong to meeting 1: ['meeting_poll_default/21']",
            response.json["message"],
        )
        self.assert_model_exists("meeting_poll_default/21", {"group_ids": None})
