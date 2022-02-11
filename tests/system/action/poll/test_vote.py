import json
from typing import Any, Dict

import requests

from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase
from tests.system.util import convert_to_test_response
from tests.util import Response


class BaseVoteTestCase(BaseActionTestCase):
    def request(
        self,
        action: str,
        data: Dict[str, Any],
        anonymous: bool = False,
        start_poll_before_vote: bool = True,
        stop_poll_after_vote: bool = True,
    ) -> Response:
        """Overwrite request method to reroute voting requests to the vote service."""
        if action == "poll.vote":
            if start_poll_before_vote:
                self.vote_service.start(data["id"])
            response = self.vote_service.vote(data)
            if stop_poll_after_vote:
                self.execute_action_internally("poll.stop", {"id": data["id"]})
            return response
        else:
            return super().request(action, data, anonymous)

    def anonymous_vote(self, payload: Dict[str, Any], id: int = 1) -> Response:
        # make request manually to prevent sending of cookie & header
        payload_json = json.dumps(payload, separators=(",", ":"))
        response = requests.post(
            url=self.vote_service.url.replace("internal", "system") + f"?id={id}",
            data=payload_json,
            headers={
                "Content-Type": "application/json",
            },
        )
        return convert_to_test_response(response)


class PollVoteTest(BaseVoteTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "meeting/113",
            {"is_active_in_organization_id": 1},
        )

    def test_vote_correct_pollmethod_Y(self) -> None:
        user_id = self.create_user("test2")
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1, user_id]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                f"user/{user_id}": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                    "vote_weight_$113": "2.000000",
                    "vote_weight_$": ["113"],
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
                    "state": Poll.STATE_STARTED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 10,
                    "max_votes_per_person": 1,
                },
                "meeting/113": {"users_enable_vote_weight": True},
            }
        )
        response = self.request(
            "poll.vote", {"id": 1, "value": {"11": 1}}, stop_poll_after_vote=False
        )
        self.assert_status_code(response, 200)
        self.login(user_id)
        response = self.request(
            "poll.vote", {"id": 1, "value": {"11": 1}}, start_poll_before_vote=False
        )
        self.assert_status_code(response, 200)
        vote = self.get_model("vote/1")
        assert vote.get("value") == "Y"
        assert vote.get("option_id") == 11
        assert vote.get("weight") == "1.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 1
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]
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
                "organization/1": {"enable_electronic_voting": True},
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
                    "state": Poll.STATE_STARTED,
                },
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
        assert (
            "Data for option 13 does not fit the poll method."
            in response.json["message"]
        )

    def test_vote_correct_pollmethod_YN(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
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
                    "state": Poll.STATE_STARTED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 10,
                    "max_votes_per_person": 1,
                },
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
        user_token = vote.get("user_token")
        vote = self.get_model("vote/2")
        assert vote.get("value") == "N"
        assert vote.get("option_id") == 12
        assert vote.get("weight") == "1.000000"
        assert vote.get("meeting_id") == 113
        assert vote.get("user_id") == 1
        assert vote.get("user_token") == user_token
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
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1, 2]

    def test_vote_wrong_votes_total(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_STARTED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_person": 1,
                },
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
                "value": {"11": 1, "12": 1},
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "The sum of your answers has to be between 1 and 1"
            in response.json["message"]
        )
        self.assert_model_not_exists("vote/1")

    def test_vote_pollmethod_Y_wrong_value(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {
                    "option_ids": [11, 12, 13],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_STARTED,
                },
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
                "value": {"11": "Y"},
            },
        )
        self.assert_status_code(response, 400)
        assert "Your vote has a wrong format" in response.json["message"]
        self.assert_model_not_exists("vote/1")

    def test_vote_no_votes_total_check_by_YNA(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "YNA",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_STARTED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_person": 1,
                },
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
                "value": {"11": "Y", "12": "A"},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")

    def test_vote_no_votes_total_check_by_YN(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
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
                    "state": Poll.STATE_STARTED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_person": 1,
                },
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
        self.assert_model_exists("vote/1")

    def test_vote_wrong_votes_total_min_case(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_STARTED,
                    "min_votes_amount": 2,
                    "max_votes_amount": 2,
                    "max_votes_per_person": 1,
                },
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
                "value": {"11": 1},
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "The sum of your answers has to be between 2 and 2"
            in response.json["message"]
        )
        self.assert_model_not_exists("vote/1")

    def test_vote_global(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
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
                    "state": Poll.STATE_STARTED,
                    "pollmethod": "YNA",
                },
            }
        )
        response = self.request(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": "N"},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(response, 200)
        response = self.request("poll.vote", {"id": 1, "user_id": 2, "value": "Y"})
        self.assert_status_code(response, 400)

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
        self.assert_model_not_exists("vote/2")
        option = self.get_model("option/11")
        assert option.get("vote_ids") == [1]
        user = self.get_model("user/1")
        assert user.get("vote_$_ids") == ["113"]
        assert user.get("vote_$113_ids") == [1]

    def test_vote_schema_problems(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "poll/1": {
                    "title": "my test poll",
                    "entitled_group_ids": [1],
                    "meeting_id": 113,
                    "pollmethod": "YNA",
                    "state": Poll.STATE_STARTED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "X"})
        self.assert_status_code(response, 400)
        assert "Global vote X is not enabled" in response.json["message"]

    def test_vote_invalid_vote_value(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {
                    "option_ids": [11],
                    "pollmethod": "YNA",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 113,
                },
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
                "value": {"11": "X"},
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Data for option 11 does not fit the poll method."
            in response.json["message"]
        )

    def test_vote_not_started_in_service(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "poll/1": {
                    "type": "named",
                    "meeting_id": 113,
                    "pollmethod": "YNA",
                    "global_yes": True,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_STARTED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$_ids": ["113"],
                    "group_$113_ids": [1],
                },
            }
        )
        response = self.request(
            "poll.vote",
            {"id": 1, "value": "Y"},
            start_poll_before_vote=False,
            stop_poll_after_vote=False,
        )
        self.assert_status_code(response, 400)
        assert "Poll does not exist" in response.json["message"]

    def test_vote_option_not_in_poll(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "poll/1": {
                    "title": "my test poll",
                    "type": "named",
                    "pollmethod": "YNA",
                    "entitled_group_ids": [1],
                    "meeting_id": 113,
                    "state": Poll.STATE_STARTED,
                },
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
        assert "Option_id 113 does not belong to the poll" in response.json["message"]

    def test_double_vote(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
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
                    "state": Poll.STATE_STARTED,
                },
            }
        )
        response = self.request(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": "N"},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(response, 200)
        response = self.request(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": "N"},
            start_poll_before_vote=False,
        )
        self.assert_status_code(response, 400)
        assert "Not the first vote" in response.json["message"]
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

    def test_check_user_in_entitled_group(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "user/1": {"is_present_in_meeting_ids": [113]},
                "poll/1": {
                    "pollmethod": "YNA",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "entitled_group_ids": [],
                    "state": Poll.STATE_STARTED,
                },
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "N"})
        self.assert_status_code(response, 400)
        assert "User 1 is not allowed to vote" in response.json["message"]

    def test_check_user_present_in_meeting(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
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
                    "state": Poll.STATE_STARTED,
                },
            }
        )
        response = self.request("poll.vote", {"id": 1, "value": "N"})
        self.assert_status_code(response, 400)
        assert "You have to be present in meeting 113" in response.json["message"]

    def test_check_str_validation(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "poll/1": {
                    "title": "my test poll",
                    "type": "named",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "pollmethod": "Y",
                    "state": Poll.STATE_STARTED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$_ids": ["113"],
                    "group_$113_ids": [1],
                },
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "X"})
        self.assert_status_code(response, 400)
        assert "Global vote X is not enabled" in response.json["message"]

    def test_default_vote_weight(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
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
                    "state": Poll.STATE_STARTED,
                },
                "meeting/113": {"users_enable_vote_weight": True},
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

    def test_vote_weight_not_enabled(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "group/1": {"user_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                    "default_vote_weight": "3.000000",
                    "vote_weight_$113": "4.200000",
                    "vote_weight_$": ["113"],
                },
                "poll/1": {
                    "title": "my test poll",
                    "option_ids": [11],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_STARTED,
                },
                "meeting/113": {"users_enable_vote_weight": False},
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


class VotePollBaseTestClass(BaseVoteTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "assignment/1": {
                    "title": "test_assignment_tcLT59bmXrXif424Qw7K",
                    "open_posts": 1,
                    "meeting_id": 113,
                },
                "meeting/113": {"is_active_in_organization_id": 1},
            }
        )
        self.create_poll()
        self.set_models(
            {
                "group/1": {"user_ids": [1]},
                "option/1": {
                    "meeting_id": 113,
                    "poll_id": 1,
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                },
                "option/2": {
                    "meeting_id": 113,
                    "poll_id": 1,
                    "yes": "0.000000",
                    "no": "0.000000",
                    "abstain": "0.000000",
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "group_$113_ids": [1],
                    "group_$_ids": ["113"],
                },
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "poll/1": {"global_option_id": 11},
            }
        )

    def create_poll(self) -> None:
        # has to be implemented by subclasses
        raise NotImplementedError()

    def start_poll(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})

    def add_option(self) -> None:
        self.set_models(
            {
                "option/3": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {"option_ids": [1, 2, 3]},
            }
        )


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
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_person": 1,
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
        self.set_models(
            {
                "user/1": {"vote_weight_$113": "4.200000", "vote_weight_$": ["113"]},
                "meeting/113": {"users_enable_vote_weight": True},
            }
        )
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
        self.assertEqual(poll.get("state"), Poll.STATE_FINISHED)
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
            stop_poll_after_vote=False,
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": "N"}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
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

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.anonymous_vote({"value": {"1": "Y"}})
        self.assert_status_code(response, 401)
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
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
            stop_poll_after_vote=False,
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
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_person": 1,
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
            stop_poll_after_vote=False,
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
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
            {"id": 1, "value": {"3": 1}},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.anonymous_vote({"value": {"1": 1}})
        self.assert_status_code(response, 401)
        self.assert_model_not_exists("vote/1")

    def test_anonymous_as_vote_user(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 0},
        )
        self.assert_status_code(response, 400)
        assert "Votes for anonymous user are not allowed" in response.json["message"]
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
            start_poll_before_vote=False,
            stop_poll_after_vote=False,
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
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_person": 1,
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
            stop_poll_after_vote=False,
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
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

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.anonymous_vote({"value": {"1": 1}})
        self.assert_status_code(response, 401)
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
            start_poll_before_vote=False,
            stop_poll_after_vote=False,
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
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_person": 1,
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
            stop_poll_after_vote=False,
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": "N"}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
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

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.anonymous_vote({"value": {"1": "Y"}})
        self.assert_status_code(response, 401)
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
        response = self.request(
            "poll.vote",
            {"value": {}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
            stop_poll_after_vote=False,
        )
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
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_person": 1,
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
            stop_poll_after_vote=False,
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
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
            start_poll_before_vote=False,
            stop_poll_after_vote=False,
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
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_person": 1,
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
            stop_poll_after_vote=False,
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(response, 400)
        self.get_model("poll/1")
        option1 = self.get_model("option/1")
        self.assertEqual(option1.get("yes"), "0.000000")
        self.assertEqual(option1.get("no"), "1.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        option2 = self.get_model("option/2")
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
            start_poll_before_vote=False,
            stop_poll_after_vote=False,
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "decoding payload: unknown vote value: `[1,2,5]`"
            in response.json["message"]
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        assert "Your vote has a wrong format" in response.json["message"]
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
        assert "decoding payload: unknown vote value:" in response.json["message"]
        self.assert_model_not_exists("vote/1")
