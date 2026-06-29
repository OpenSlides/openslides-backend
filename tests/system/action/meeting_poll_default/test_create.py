from tests.system.action.base import BaseActionTestCase


class MeetingPollDefaultCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(17)

    def test_create_simple(self) -> None:
        response = self.request(
            "meeting_poll_default.create",
            {"meeting_id": 17, "used_as_motion_poll_config_in_meeting_id": 17},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_poll_default/1",
            {
                "meeting_id": 17,
                "used_as_motion_poll_config_in_meeting_id": 17,
                "ballot_paper_selection": "custom_number",
                "ballot_paper_number": 8,
                "sort_result_by_votes": True,
                "allow_abstain": True,
                "allow_nota": False,
                "strike_out": False,
                "onehundred_percent_base": "valid",
                "visibility": None,
                "group_ids": None,
                "display_chart": None,
            },
        )
        self.assert_model_exists(
            "meeting/17", {"poll_default_ids": [1], "motion_poll_config_id": 1}
        )

    def test_create_set_all_fields(self) -> None:
        data = {
            "meeting_id": 17,
            "used_as_topic_poll_config_in_meeting_id": 17,
            "ballot_paper_selection": "number_of_all_participants",
            "ballot_paper_number": 6,
            "sort_result_by_votes": False,
            "visibility": "named",
            "allow_abstain": False,
            "allow_nota": True,
            "strike_out": True,
            "onehundred_percent_base": "cast",
            "group_ids": [19],
            "display_chart": "pie",
        }
        response = self.request("meeting_poll_default.create", data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_poll_default/1", data)
        self.assert_model_exists(
            "meeting/17", {"poll_default_ids": [1], "topic_poll_config_id": 1}
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "meeting_poll_default.create",
            {
                "meeting_id": 17,
                "used_as_motion_poll_config_in_meeting_id": 17,
                "wrong_field": "test",
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )
        self.assert_model_not_exists("meeting_poll_default/1")

    def test_create_empty_data(self) -> None:
        response = self.request("meeting_poll_default.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id'] properties",
            response.json["message"],
        )
        self.assert_model_not_exists("meeting_poll_default/1")

    def test_create_no_poll_type_fields(self) -> None:
        response = self.request("meeting_poll_default.create", {"meeting_id": 17})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "One of the fields ['used_as_assignment_poll_config_in_meeting_id', 'used_as_motion_poll_config_in_meeting_id', 'used_as_topic_poll_config_in_meeting_id'] must be set.",
            response.json["message"],
        )
        self.assert_model_not_exists("meeting_poll_default/1")

    def test_create_multiple_poll_type_fields(self) -> None:
        response = self.request(
            "meeting_poll_default.create",
            {
                "meeting_id": 17,
                "used_as_assignment_poll_config_in_meeting_id": 17,
                "used_as_topic_poll_config_in_meeting_id": 17,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Only one of ['used_as_assignment_poll_config_in_meeting_id', 'used_as_motion_poll_config_in_meeting_id', 'used_as_topic_poll_config_in_meeting_id'] can be set.",
            response.json["message"],
        )
        self.assert_model_not_exists("meeting_poll_default/1")

    def test_create_meeting_id_mismatch(self) -> None:
        self.create_meeting()
        response = self.request(
            "meeting_poll_default.create",
            {"meeting_id": 17, "used_as_assignment_poll_config_in_meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Values in fields 'used_as_assignment_poll_config_in_meeting_id' and 'meeting_id' don't match.",
            response.json["message"],
        )
        self.assert_model_not_exists("meeting_poll_default/1")

    def test_create_duplicate(self) -> None:
        response = self.request(
            "meeting_poll_default.create",
            {"meeting_id": 17, "used_as_assignment_poll_config_in_meeting_id": 17},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_poll_default/1")

        response = self.request(
            "meeting_poll_default.create",
            {"meeting_id": 17, "used_as_assignment_poll_config_in_meeting_id": 17},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("meeting_poll_default/2")
        self.assertEqual(
            "'used_as_assignment_poll_config_in_meeting_id' already exists in meeting/17.",
            response.json["message"],
        )
