from tests.system.action.base import BaseActionTestCase


class PollCreateTest(BaseActionTestCase):
    def test_create_correct(self) -> None:
        self.create_model("meeting/112", {"name": "meeting_112"})
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 112,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "amount_global_yes": "1.000000",
                "amount_global_no": "1.250000",
                "amount_global_abstain": "2.500000",
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("title") == "test"
        assert poll.get("type") == "analog"
        assert poll.get("pollmethod") == "Y"
        assert poll.get("meeting_id") == 112
        assert poll.get("option_ids") == [1]
        assert poll.get("global_option_id") == 2
        assert poll.get("state") == "finished"
        option = self.get_model("option/1")
        assert option.get("text") == "test2"
        assert option.get("poll_id") == 1
        assert option.get("meeting_id") == 112
        global_option = self.get_model("option/2")
        assert global_option.get("text") == "global option"
        assert global_option.get("used_as_global_option_in_poll_id") == 1
        assert global_option.get("meeting_id") == 112
        assert global_option.get("yes") == "1.000000"
        assert global_option.get("no") == "1.250000"
        assert global_option.get("abstain") == "2.500000"

    def test_create_three_options(self) -> None:
        self.create_model("meeting/112", {"name": "meeting_112"})
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YNA",
                "options": [
                    {"text": "test2", "Y": "10.000000"},
                    {"text": "test3", "N": "0.999900"},
                    {"text": "test4", "N": "11.000000"},
                ],
                "meeting_id": 112,
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("title") == "test"
        assert poll.get("type") == "analog"
        assert poll.get("pollmethod") == "YNA"
        assert poll.get("meeting_id") == 112
        assert poll.get("option_ids") == [1, 2, 3]
        assert poll.get("global_option_id") == 4
        option = self.get_model("option/1")
        assert option.get("text") == "test2"
        assert option.get("poll_id") == 1
        assert option.get("meeting_id") == 112
        assert option.get("yes") == "10.000000"
        assert option.get("weight") == 1
        option_2 = self.get_model("option/2")
        assert option_2.get("text") == "test3"
        assert option_2.get("poll_id") == 1
        assert option_2.get("meeting_id") == 112
        assert option_2.get("no") == "0.999900"
        assert option_2.get("weight") == 2
        option_3 = self.get_model("option/3")
        assert option_3.get("text") == "test4"
        assert option_3.get("poll_id") == 1
        assert option_3.get("meeting_id") == 112
        assert option_3.get("no") == "11.000000"
        assert option_3.get("weight") == 3
        option_4 = self.get_model("option/4")
        assert option_4.get("text") == "global option"
        assert option_4.get("used_as_global_option_in_poll_id") == 1
        assert option_4.get("meeting_id") == 112
        assert option_4.get("weight") == 1
