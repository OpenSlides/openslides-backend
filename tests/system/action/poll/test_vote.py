from tests.system.action.base import BaseActionTestCase


class PollVoteTest(BaseActionTestCase):
    def test_vote_correct_pollmethod_Y(self) -> None:
        self.create_model("group/1", {"user_ids": [1, 2]})
        self.create_model("option/11", {"meeting_id": 113, "poll_id": 1})
        self.create_model(
            "user/2", {"username": "test2", "is_present_in_meeting_ids": [113]}
        )
        self.update_model("user/1", {"is_present_in_meeting_ids": [113]})
        self.create_model(
            "poll/1",
            {
                "title": "my test poll",
                "option_ids": [11],
                "pollmethod": "Y",
                "meeting_id": 113,
                "entitled_group_ids": [1],
            },
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 1, "value": {"11": 1}}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "Y"
        assert vote.get("option_id") == 11
        assert vote.get("weight") == "1.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 1
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1]
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 2, "value": {"11": 0}}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/2")
        assert vote.get("value") == "Y"
        assert vote.get("option_id") == 11
        assert vote.get("weight") == "0.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 2
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1, 2]
        user = self.get_model("user/2")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [2]

    def test_vote_correct_pollmethod_YN(self) -> None:
        self.create_model("group/1", {"user_ids": [1]})
        self.create_model("option/11", {"meeting_id": 113, "poll_id": 1})
        self.create_model("option/12", {"meeting_id": 113, "poll_id": 1})
        self.create_model("option/13", {"meeting_id": 113, "poll_id": 1})
        self.create_model(
            "poll/1",
            {
                "title": "my test poll",
                "option_ids": [11, 12, 13],
                "pollmethod": "YN",
                "meeting_id": 113,
                "entitled_group_ids": [1],
            },
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        self.update_model("user/1", {"is_present_in_meeting_ids": [113]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [
                        {
                            "id": 1,
                            "user_id": 1,
                            "value": {"11": "Y", "12": "N", "13": "A"},
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "Y"
        assert vote.get("option_id") == 11
        assert vote.get("weight") == "1.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 1
        vote = self.get_model("vote/2")
        assert vote.get("value") == "N"
        assert vote.get("option_id") == 12
        assert vote.get("weight") == "1.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 1
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1]
        option = self.get_model("option/12")
        assert option.get("vote_ids") == [2]
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113", "113"]
        assert user.get("vote_$113_ids") == [1, 2]

    def test_vote_global(self) -> None:
        self.create_model("group/1", {"user_ids": [1, 2]})
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.create_model(
            "user/2", {"username": "test2", "is_present_in_meeting_ids": [113]}
        )
        self.update_model("user/1", {"is_present_in_meeting_ids": [113]})
        self.create_model(
            "poll/1",
            {
                "title": "my test poll",
                "global_option_id": 11,
                "global_no": True,
                "global_yes": False,
                "global_abstain": False,
                "meeting_id": 113,
                "entitled_group_ids": [1],
            },
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 1, "value": "N"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "N"
        assert vote.get("option_id") == 11
        assert vote.get("weight") == "1.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 1
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1]
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 2, "value": "Y"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("vote/2")
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1]
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]

    def test_vote_schema_problems(self) -> None:
        self.create_model("group/1", {"user_ids": [1]})
        self.create_model(
            "poll/1", {"title": "my test poll", "entitled_group_ids": [1]}
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        self.update_model("user/1", {"is_present_in_meeting_ids": [113]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 1, "value": "X"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert (
            "data.value must be valid by one of anyOf definition"
            in response.data.decode()
        )

    def test_vote_for_analog_type(self) -> None:
        self.create_model("group/1", {"user_ids": [1]})
        self.create_model(
            "poll/1",
            {"title": "my test poll", "type": "analog", "entitled_group_ids": [1]},
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        self.update_model("user/1", {"is_present_in_meeting_ids": [113]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 1, "value": "Y"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "poll.vote is not allowed for analog voting." in response.data.decode()

    def test_vote_option_not_in_poll(self) -> None:
        self.create_model("group/1", {"user_ids": [1]})
        self.create_model(
            "poll/1",
            {
                "title": "my test poll",
                "type": "named",
                "entitled_group_ids": [1],
                "meeting_id": 113,
            },
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        self.update_model("user/1", {"is_present_in_meeting_ids": [113]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [
                        {
                            "id": 1,
                            "user_id": 1,
                            "value": {"113": "Y"},
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Option 113 not in options of the poll." in response.data.decode()

    def test_double_vote(self) -> None:
        self.create_model("group/1", {"user_ids": [1, 2]})
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.create_model(
            "user/2", {"username": "test2", "is_present_in_meeting_ids": [113]}
        )
        self.update_model("user/1", {"is_present_in_meeting_ids": [113]})
        self.create_model(
            "poll/1",
            {
                "title": "my test poll",
                "global_option_id": 11,
                "global_no": True,
                "global_yes": False,
                "global_abstain": False,
                "meeting_id": 113,
                "entitled_group_ids": [1],
            },
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 1, "value": "N"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "N"
        assert vote.get("option_id") == 11
        assert vote.get("weight") == "1.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 1
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1]
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 1, "value": "N"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Only one vote per poll per user allowed." in response.data.decode()

    def test_check_user_in_entitled_group(self) -> None:
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.update_model("user/1", {"is_present_in_meeting_ids": [113]})
        self.create_model(
            "poll/1",
            {
                "title": "my test poll",
                "global_option_id": 11,
                "global_no": True,
                "global_yes": False,
                "global_abstain": False,
                "meeting_id": 113,
                "entitled_group_ids": [],
            },
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 1, "value": "N"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "User is not allowed to vote." in response.data.decode()

    def test_check_user_present_in_meeting(self) -> None:
        self.create_model("group/1", {"user_ids": [1]})
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.create_model(
            "poll/1",
            {
                "title": "my test poll",
                "global_option_id": 11,
                "global_no": True,
                "global_yes": False,
                "global_abstain": False,
                "meeting_id": 113,
                "entitled_group_ids": [1],
            },
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.vote",
                    "data": [{"id": 1, "user_id": 1, "value": "N"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "User is not present in the meeting." in response.data.decode()
