import pytest

from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase


class PollVoteTest(BaseActionTestCase):
    def test_vote_correct_pollmethod_Y(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1, 2]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "user/2": {
                    "username": "test2",
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                    "vote_weight_$113": "2.000000",
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
                "poll/1": {
                    "title": "my test poll",
                    "option_ids": [11],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                },
                "meeting/113": {"name": "my meeting"},
            }
        )
        response = self.request(
            "poll.vote", {"id": 1, "user_id": 1, "value": {"11": 1}}
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
        assert option.get("yes") == "1.000000"
        assert option.get("no") == "0.000000"
        assert option.get("abstain") == "0.000000"
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]
        response = self.request(
            "poll.vote", {"id": 1, "user_id": 2, "value": {"11": 1}}
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/2")
        assert vote.get("value") == "Y"
        assert vote.get("option_id") == 11
        assert vote.get("weight") == "2.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 2
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1, 2]
        assert option.get("yes") == "3.000000"
        assert option.get("no") == "0.000000"
        assert option.get("abstain") == "0.000000"
        user = self.get_model("user/2")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [2]

    def test_value_check(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "YN",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                },
                "meeting/113": {"name": "my meeting"},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
            }
        )
        response = self.request(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"11": "Y", "12": "N", "13": "A"},
            },
        )
        self.assert_status_code(response, 400)
        assert "Option 13 has not a right value. (int, str)." in response.data.decode()

    def test_vote_correct_pollmethod_YN(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "YN",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                },
                "meeting/113": {"name": "my meeting"},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
            }
        )
        response = self.request(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"11": "Y", "12": "N"},
            },
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
        assert option.get("yes") == "1.000000"
        assert option.get("no") == "0.000000"
        assert option.get("abstain") == "0.000000"
        option = self.get_model("option/12")
        assert option.get("vote_ids") == [2]
        assert option.get("yes") == "0.000000"
        assert option.get("no") == "1.000000"
        assert option.get("abstain") == "0.000000"
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113", "113"]
        assert user.get("vote_$113_ids") == [1, 2]

    def test_vote_global(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1, 2]},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "user/2": {
                    "username": "test2",
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
                "poll/1": {
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "pollmethod": "YNA",
                },
                "meeting/113": {"name": "my meeting"},
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "N"})
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "N"
        assert vote.get("option_id") == 11
        assert vote.get("weight") == "1.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 1
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1]
        assert option.get("yes") == "0.000000"
        assert option.get("no") == "1.000000"
        assert option.get("abstain") == "0.000000"
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]

        response = self.request("poll.vote", {"id": 1, "user_id": 2, "value": "Y"})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("vote/2")
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1]
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]

    def test_vote_schema_problems(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1]},
                "poll/1": {
                    "title": "my test poll",
                    "entitled_group_ids": [1],
                    "meeting_id": 113,
                    "pollmethod": "YNA",
                },
                "meeting/113": {"name": "my meeting"},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "X"})
        self.assert_status_code(response, 400)
        assert "Option value X is not in 'YNA'" in response.data.decode()

    def test_vote_for_analog_type(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1]},
                "poll/1": {
                    "title": "my test poll",
                    "type": "analog",
                    "entitled_group_ids": [1],
                },
                "meeting/113": {"name": "my meeting"},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$_ids": ["113"],
                    "group_$113_ids": [1],
                },
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "Y"})
        self.assert_status_code(response, 400)
        assert "poll.vote is not allowed for analog voting." in response.data.decode()

    def test_vote_option_not_in_poll(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1]},
                "poll/1": {
                    "title": "my test poll",
                    "type": "named",
                    "entitled_group_ids": [1],
                    "meeting_id": 113,
                },
                "meeting/113": {"name": "my meeting"},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
            }
        )
        response = self.request(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"113": "Y"},
            },
        )
        self.assert_status_code(response, 400)
        assert "Option 113 not in options of the poll." in response.data.decode()

    def test_double_vote(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1, 2]},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "user/2": {
                    "username": "test2",
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
                "poll/1": {
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "pollmethod": "YN",
                },
                "meeting/113": {"name": "my meeting"},
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "N"})
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

        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "N"})
        self.assert_status_code(response, 400)
        assert "Only one vote per poll per user allowed." in response.data.decode()

    def test_check_user_in_entitled_group(self) -> None:
        self.set_models(
            {
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "user/1": {"is_present_in_meeting_ids": [113]},
                "poll/1": {
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "entitled_group_ids": [],
                },
                "meeting/113": {"name": "my meeting"},
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "N"})
        self.assert_status_code(response, 400)
        assert "User is not allowed to vote." in response.data.decode()

    def test_check_user_present_in_meeting(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1]},
                "user/1": {"group_$_ids": ["113"], "group_$113_ids": [1]},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "poll/1": {
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                },
                "meeting/113": {"name": "my meeting"},
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "N"})
        self.assert_status_code(response, 400)
        assert "User is not present in the meeting." in response.data.decode()

    def test_check_str_validation(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1]},
                "poll/1": {
                    "title": "my test poll",
                    "type": "named",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "pollmethod": "Y",
                },
                "meeting/113": {"name": "my meeting"},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$_ids": ["113"],
                    "group_$113_ids": [1],
                },
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "X"})
        self.assert_status_code(response, 400)
        assert "Option value X is not in 'YNA'." in response.data.decode()

    def test_default_vote_weight(self) -> None:
        self.set_models(
            {
                "group/1": {"user_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                    "default_vote_weight": "3.000000",
                },
                "poll/1": {
                    "title": "my test poll",
                    "option_ids": [11],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                },
                "meeting/113": {"name": "my meeting"},
            }
        )
        response = self.request(
            "poll.vote", {"id": 1, "user_id": 1, "value": {"11": 1}}
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "Y"
        assert vote.get("option_id") == 11
        assert vote.get("weight") == "3.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 1
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1]
        assert option.get("yes") == "3.000000"
        assert option.get("no") == "0.000000"
        assert option.get("abstain") == "0.000000"
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]


class VotePollBaseTestClass(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "assignment/1",
            {
                "title": "test_assignment_tcLT59bmXrXif424Qw7K",
                "open_posts": 1,
            },
        )
        self.create_poll()
        self.create_model("meeting/113", {"name": "my meeting"})
        self.create_model("group/1", {"user_ids": [1]})
        self.create_model(
            "option/1",
            {
                "meeting_id": 113,
                "poll_id": 1,
                "yes": "0.000000",
                "no": "0.000000",
                "abstain": "0.000000",
            },
        )
        self.create_model(
            "option/2",
            {
                "meeting_id": 113,
                "poll_id": 1,
                "yes": "0.000000",
                "no": "0.000000",
                "abstain": "0.000000",
            },
        )
        self.update_model(
            "user/1",
            {
                "is_present_in_meeting_ids": [113],
                "group_$113_ids": [1],
                "group_$_ids": ["113"],
            },
        )

    def create_poll(self) -> None:
        # has to be implemented by subclasses
        raise NotImplementedError()

    def start_poll(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})

    def add_option(self) -> None:
        self.create_model("option/3", {"meeting_id": 113, "poll_id": 1})
        self.update_model("poll/1", {"option_ids": [1, 2, 3]})


class VotePollAnalogYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_04k0y4TwPLpJKaSvIGm1",
                "pollmethod": "YNA",
                "type": Poll.TYPE_ANALOG,
                "state": Poll.STATE_CREATED,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
            },
        )

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {
                "value": {
                    "1": {"Y": "1", "N": "2.35", "A": "-1"},
                    "2": {"Y": "30", "N": "-2", "A": "8.93"},
                },
                "user_id": 1,
                "id": 1,
            },
        )
        self.assert_status_code(response, 400)
        assert "poll.vote is not allowed for analog voting." in response.data.decode()


class VotePollNamedYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_OkHAIvOSIcpFnCxbaL6v",
                "pollmethod": "YNA",
                "type": Poll.TYPE_NAMED,
                "state": Poll.STATE_CREATED,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votescast": "0.000000",
                "votesvalid": "0.000000",
                "votesinvalid": "0.000000",
            },
        )

    def test_vote(self) -> None:
        self.add_option()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_count("vote", 113, 3)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertIn(1, poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        option3 = self.get_model("option/3")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "1.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")
        self.assertEqual(option3.get("yes"), "0.000000")
        self.assertEqual(option3.get("no"), "0.000000")
        self.assertEqual(option3.get("abstain"), "1.000000")

    def test_vote_with_voteweight(self) -> None:
        # config["users_activate_vote_weight"] = True
        self.update_model("user/1", {"vote_weight_$113": "4.200000"})
        self.add_option()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_count("vote", 113, 3)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "4.200000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        option3 = self.get_model("option/3")
        self.assertEqual(option1.get("yes"), "4.200000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "4.200000")
        self.assertEqual(option2.get("abstain"), "0.000000")
        self.assertEqual(option3.get("yes"), "0.000000")
        self.assertEqual(option3.get("no"), "0.000000")
        self.assertEqual(option3.get("abstain"), "4.200000")

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/2")
        vote = self.get_model("vote/1")
        self.assertEqual(vote.get("value"), "Y")

    def test_too_many_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    @pytest.mark.skip()
    def test_no_permissions(self) -> None:
        self.start_poll()
        # self.make_admin_delegate()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 0},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollNamedY(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_Zrvh146QAdq7t6iSDwZk",
                "pollmethod": "Y",
                "type": Poll.TYPE_NAMED,
                "state": Poll.STATE_CREATED,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
            },
        )

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_not_exists("vote/2")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertIn(1, poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_global_yes(self) -> None:
        self.start_poll()
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.update_model("poll/1", {"global_option_id": 11})
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "1.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "0.000000")

    def test_global_yes_forbidden(self) -> None:
        self.update_model("poll/1", {"global_yes": False})
        self.start_poll()
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_global_no(self) -> None:
        self.start_poll()
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.update_model("poll/1", {"global_option_id": 11})
        response = self.request("poll.vote", {"value": "N", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "1.000000")
        self.assertEqual(option.get("abstain"), "0.000000")

    def test_global_no_forbidden(self) -> None:
        self.update_model("poll/1", {"global_no": False})
        self.start_poll()
        response = self.request("poll.vote", {"value": "N", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_global_abstain(self) -> None:
        self.start_poll()
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.update_model("poll/1", {"global_option_id": 11})

        response = self.request("poll.vote", {"value": "A", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "1.000000")

    def test_global_abstain_forbidden(self) -> None:
        self.update_model("poll/1", {"global_abstain": False})
        self.start_poll()
        response = self.request("poll.vote", {"value": "A", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_negative_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_too_many_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 1, "3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"3": 1}},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    @pytest.mark.skip()
    def test_no_permissions(self) -> None:
        self.start_poll()
        # self.make_admin_delegate()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 0},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollNamedN(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_4oi49ckKFk39SDIfj30s",
                "pollmethod": "N",
                "type": Poll.TYPE_NAMED,
                "state": Poll.STATE_CREATED,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
            },
        )

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_not_exists("vote/2")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertTrue(1 in poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "0.000000")
        self.assertEqual(option1.get("no"), "1.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_change_vote(self) -> None:
        self.add_option()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "0.000000")
        self.assertEqual(option1.get("no"), "1.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_global_yes(self) -> None:
        self.start_poll()
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.update_model("poll/1", {"global_option_id": 11})
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "1.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "0.000000")

    def test_global_yes_forbidden(self) -> None:
        self.update_model("poll/1", {"global_yes": False})
        self.start_poll()
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_global_no(self) -> None:
        self.start_poll()
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.update_model("poll/1", {"global_option_id": 11})
        response = self.request("poll.vote", {"value": "N", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "1.000000")
        self.assertEqual(option.get("abstain"), "0.000000")

    def test_global_no_forbidden(self) -> None:
        self.update_model("poll/1", {"global_no": False})
        self.start_poll()
        response = self.request("poll.vote", {"value": "N", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_global_abstain(self) -> None:
        self.start_poll()
        self.create_model(
            "option/11", {"meeting_id": 113, "used_as_global_option_in_poll_id": 1}
        )
        self.update_model("poll/1", {"global_option_id": 11})
        response = self.request("poll.vote", {"value": "A", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "1.000000")

    def test_global_abstain_forbidden(self) -> None:
        self.update_model("poll/1", {"global_abstain": False})
        self.start_poll()
        response = self.request("poll.vote", {"value": "A", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_negative_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    @pytest.mark.skip()
    def test_no_permissions(self) -> None:
        self.start_poll()
        # self.make_admin_delegate()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 2},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollPseudoanonymousYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_OkHAIvOSIcpFnCxbaL6v",
                "pollmethod": "YNA",
                "type": Poll.TYPE_PSEUDOANONYMOUS,
                "state": Poll.STATE_CREATED,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
            },
        )

    def test_vote(self) -> None:
        self.add_option()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_count("vote", 113, 3)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        option3 = self.get_model("option/3")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "1.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")
        self.assertEqual(option3.get("yes"), "0.000000")
        self.assertEqual(option3.get("no"), "0.000000")
        self.assertEqual(option3.get("abstain"), "1.000000")

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        option1 = self.get_model("option/1")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")

    def test_too_many_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_partial_vote(self) -> None:
        self.add_option()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    @pytest.mark.skip()
    def test_no_permissions(self) -> None:
        self.start_poll()
        # self.make_admin_delegate()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 2},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_value(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_value_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_value(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollPseudoanonymousY(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_Zrvh146QAdq7t6iSDwZk",
                "pollmethod": "Y",
                "type": Poll.TYPE_PSEUDOANONYMOUS,
                "state": Poll.STATE_CREATED,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
            },
        )

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_not_exists("vote/2")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertTrue(1 in poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")
        vote = self.get_model("vote/1")
        self.assertIsNone(vote.get("user_id"))

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.get_model("poll/1")
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_negative_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"value": [1, 2, 5]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollPseudoAnonymousN(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_wWPOVJgL9afm83eamf3e",
                "pollmethod": "N",
                "type": Poll.TYPE_PSEUDOANONYMOUS,
                "state": Poll.STATE_CREATED,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
            },
        )

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"id": 1, "value": {"1": 1, "2": 0}, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_not_exists("vote/2")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertTrue(1 in poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "0.000000")
        self.assertEqual(option1.get("no"), "1.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")
        vote = self.get_model("vote/1")
        self.assertIsNone(vote.get("user_id"))

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.get_model("poll/1")
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "0.000000")
        self.assertEqual(option1.get("no"), "1.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_negative_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", {"is_present_in_meeting_ids": []})

        response = self.request(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": {"1": 1}},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {})
        self.assert_status_code(response, 400)
        assert (
            "data must contain ['id', 'user_id', 'value'] properties"
            in response.data.decode()
        )
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        assert "data.value must be object or string" in response.data.decode()
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        assert "Option 1 has not a right value. (int, str)." in response.data.decode()
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"id": 1, "value": {"1": [None]}, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        assert "Option 1 has not a right value. (int, str)." in response.data.decode()
        self.assert_model_not_exists("vote/1")
