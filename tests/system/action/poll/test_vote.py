from decimal import Decimal
from typing import Any

import requests
import simplejson as json

from openslides_backend.models.models import Poll
from openslides_backend.services.database.interface import PartialModel
from tests.system.util import convert_to_test_response
from tests.util import Response

from .base_poll_test import BasePollTestCase


class BaseVoteTestCase(BasePollTestCase):
    def request(
        self,
        action: str,
        data: dict[str, Any],
        anonymous: bool = False,
        lang: str | None = None,
        internal: bool | None = None,
        start_poll_before_vote: bool = True,
        stop_poll_after_vote: bool = True,
    ) -> Response:
        """Overwrite request method to reroute voting requests to the vote service."""
        if action == "poll.vote":
            if start_poll_before_vote:
                self.execute_action_internally("poll.start", {"id": data["id"]})
            response = self.vote_service.vote(data)
            if stop_poll_after_vote:
                self.execute_action_internally("poll.stop", {"id": data["id"]})
            return response
        else:
            return super().request(action, data, anonymous, lang, internal)

    def anonymous_vote(self, payload: dict[str, Any], id: int = 1) -> Response:
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
        self.create_meeting(113)
        self.create_motion(113, 1)

    def create_poll_with_3_options(self, poll_data: PartialModel = {}) -> None:
        self.set_models(
            {
                "meeting/113": {"present_user_ids": [1]},
                "group/113": {"meeting_user_ids": [11], "poll_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "pollmethod": "YN",
                    "meeting_id": 113,
                    "state": Poll.STATE_CREATED,
                    "backend": "fast",
                    "type": "named",
                    "onehundred_percent_base": "YNA",
                    **poll_data,
                },
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
            }
        )

    def test_vote_correct_pollmethod_Y(self) -> None:
        user_id = self.create_user("test2")
        self.set_models(
            {
                "group/113": {"meeting_user_ids": [11, 12], "poll_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "meeting_user/11": {
                    "meeting_id": 113,
                    "user_id": 1,
                },
                "meeting_user/12": {
                    "meeting_id": 113,
                    "user_id": user_id,
                    "vote_weight": Decimal("2.000000"),
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "state": Poll.STATE_CREATED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 10,
                    "max_votes_per_option": 1,
                    "backend": "fast",
                    "type": "named",
                    "onehundred_percent_base": "YNA",
                },
                "meeting/113": {
                    "users_enable_vote_weight": True,
                    "present_user_ids": [1, 2],
                },
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
        for i in range(1, 3):
            vote = self.assert_model_exists(
                f"vote/{i}", {"value": "Y", "option_id": 11, "meeting_id": 113}
            )
            user_id = vote.get("user_id", 0)
            assert user_id == vote.get("delegated_user_id")
            self.assert_model_exists(
                f"user/{user_id}",
                {
                    "poll_voted_ids": [1],
                    "delegated_vote_ids": [i],
                    "vote_ids": [vote["id"]],
                },
            )
            assert vote.get("weight") == Decimal(f"{user_id}.000000")
        self.assert_model_exists(
            "option/11",
            {
                "vote_ids": [1, 2],
                "yes": Decimal("3.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

    def test_value_check(self) -> None:
        self.create_poll_with_3_options(
            {
                "min_votes_amount": 1,
                "max_votes_amount": 10,
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
        self.create_poll_with_3_options(
            {
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
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
        vote = self.assert_model_exists(
            "vote/1",
            {
                "value": "Y",
                "option_id": 11,
                "weight": Decimal("1.000000"),
                "meeting_id": 113,
                "user_id": 1,
                "delegated_user_id": 1,
            },
        )
        user_token = vote.get("user_token")
        vote = self.assert_model_exists(
            "vote/2",
            {
                "value": "N",
                "option_id": 12,
                "weight": Decimal("1.000000"),
                "meeting_id": 113,
                "user_id": 1,
                "delegated_user_id": 1,
            },
        )
        assert vote.get("user_token") == user_token
        self.assert_model_exists(
            "option/11",
            {
                "vote_ids": [1],
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/12",
            {
                "vote_ids": [2],
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

    def test_vote_wrong_votes_total(self) -> None:
        self.create_poll_with_3_options(
            {
                "pollmethod": "Y",
                "min_votes_amount": 1,
                "max_votes_amount": 1,
                "max_votes_per_option": 1,
                "onehundred_percent_base": "Y",
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
        self.create_poll_with_3_options({"pollmethod": "Y"})
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
        self.create_poll_with_3_options(
            {
                "pollmethod": "YNA",
                "min_votes_amount": 1,
                "max_votes_amount": 2,
                "max_votes_per_option": 1,
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

    def test_vote_no_votes_total_check_by_YNA_max_votes_error(self) -> None:
        self.create_poll_with_3_options(
            {
                "pollmethod": "YNA",
                "min_votes_amount": 1,
                "max_votes_amount": 1,
                "max_votes_per_option": 1,
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
        self.assert_status_code(response, 400)
        assert "You have to select between 1 and 1 options" in response.json["message"]

    def test_vote_no_votes_total_check_by_YN(self) -> None:
        self.create_poll_with_3_options(
            {"max_votes_amount": 10, "max_votes_per_option": 1}
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
        self.create_poll_with_3_options(
            {
                "pollmethod": "Y",
                "min_votes_amount": 2,
                "max_votes_amount": 2,
                "max_votes_per_option": 1,
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
        self.create_user("test2")
        self.set_models(
            {
                "meeting/113": {"present_user_ids": [1, 2]},
                "group/113": {"meeting_user_ids": [11, 12], "poll_ids": [1]},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
                "meeting_user/12": {"user_id": 2, "meeting_id": 113},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "state": Poll.STATE_CREATED,
                    "pollmethod": "YNA",
                    "backend": "fast",
                    "type": "named",
                    "onehundred_percent_base": "Y",
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

        self.assert_model_exists(
            "vote/1",
            {
                "value": "N",
                "option_id": 11,
                "weight": Decimal("1.000000"),
                "meeting_id": 113,
                "user_id": 1,
            },
        )
        self.assert_model_exists(
            "option/11",
            {
                "vote_ids": [1],
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "user/1",
            {
                "poll_voted_ids": [1],
                "delegated_vote_ids": [1],
                "vote_ids": [1],
            },
        )
        self.assert_model_not_exists("vote/2")

    def test_vote_schema_problems(self) -> None:
        self.set_models(
            {
                "meeting/113": {"present_user_ids": [1]},
                "group/113": {"meeting_user_ids": [11], "poll_ids": [1]},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "meeting_id": 113,
                    "pollmethod": "YNA",
                    "state": Poll.STATE_CREATED,
                    "backend": "fast",
                    "type": "named",
                    "onehundred_percent_base": "YNA",
                },
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "X"})
        self.assert_status_code(response, 400)
        assert "Global vote X is not enabled" in response.json["message"]

    def test_vote_invalid_vote_value(self) -> None:
        self.set_models(
            {
                "meeting/113": {"present_user_ids": [1]},
                "group/113": {"meeting_user_ids": [11], "poll_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "option_ids": [11],
                    "pollmethod": "YNA",
                    "meeting_id": 113,
                    "state": Poll.STATE_CREATED,
                    "meeting_id": 113,
                    "backend": "fast",
                    "type": "named",
                    "title": "Poll 1",
                    "onehundred_percent_base": "YNA",
                },
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
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
                "meeting/113": {"present_user_ids": [1]},
                "group/113": {"meeting_user_ids": [11], "poll_ids": [1]},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "type": "named",
                    "meeting_id": 113,
                    "pollmethod": "YNA",
                    "global_yes": True,
                    "state": Poll.STATE_CREATED,
                    "backend": "fast",
                    "type": "named",
                    "title": "Poll 1",
                    "onehundred_percent_base": "YNA",
                },
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
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
        self.create_poll_with_3_options(
            {"pollmethod": "YNA", "onehundred_percent_base": "Y"}
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
        self.create_user("test2")
        self.set_models(
            {
                "meeting/113": {"present_user_ids": [1]},
                "group/113": {"meeting_user_ids": [11, 12], "poll_ids": [1]},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
                "meeting_user/12": {"user_id": 2, "meeting_id": 113},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "pollmethod": "YN",
                    "state": Poll.STATE_CREATED,
                    "backend": "fast",
                    "type": "named",
                    "onehundred_percent_base": "Y",
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
        self.assert_model_exists(
            "vote/1",
            {
                "value": "N",
                "option_id": 11,
                "weight": Decimal("1.000000"),
                "meeting_id": 113,
                "user_id": 1,
                "delegated_user_id": 1,
            },
        )
        self.assert_model_exists("option/11", {"vote_ids": [1]})
        self.assert_model_exists(
            "user/1",
            {"poll_voted_ids": [1], "vote_ids": [1], "delegated_vote_ids": [1]},
        )

    def test_check_user_in_entitled_group(self) -> None:
        self.set_models(
            {
                "meeting/113": {"present_user_ids": [1]},
                "group/113": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "pollmethod": "YNA",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "state": Poll.STATE_CREATED,
                    "backend": "fast",
                    "type": "named",
                    "title": "Poll 1",
                    "onehundred_percent_base": "YNA",
                },
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "N"})
        self.assert_status_code(response, 400)
        assert "User 1 is not allowed to vote" in response.json["message"]

    def test_check_user_present_in_meeting(self) -> None:
        self.set_models(
            {
                "group/113": {"meeting_user_ids": [11], "poll_ids": [1]},
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "state": Poll.STATE_CREATED,
                    "backend": "fast",
                    "type": "named",
                    "pollmethod": "YNA",
                    "onehundred_percent_base": "Y",
                },
            }
        )
        response = self.request("poll.vote", {"id": 1, "value": "N"})
        self.assert_status_code(response, 400)
        assert "You have to be present in meeting 113" in response.json["message"]

    def test_check_str_validation(self) -> None:
        self.set_models(
            {
                "meeting/113": {"present_user_ids": [1]},
                "group/113": {"meeting_user_ids": [11], "poll_ids": [1]},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "type": "named",
                    "meeting_id": 113,
                    "pollmethod": "Y",
                    "state": Poll.STATE_CREATED,
                    "backend": "fast",
                    "onehundred_percent_base": "Y",
                },
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
            }
        )
        response = self.request("poll.vote", {"id": 1, "user_id": 1, "value": "X"})
        self.assert_status_code(response, 400)
        assert "Global vote X is not enabled" in response.json["message"]

    def test_default_vote_weight(self) -> None:
        self.set_models(
            {
                "group/113": {"meeting_user_ids": [11], "poll_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "user/1": {"default_vote_weight": Decimal("3.000000")},
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "state": Poll.STATE_CREATED,
                    "max_votes_per_option": 1,
                    "backend": "fast",
                    "type": "named",
                    "onehundred_percent_base": "Y",
                },
                "meeting/113": {
                    "users_enable_vote_weight": True,
                    "present_user_ids": [1],
                },
            }
        )
        response = self.request(
            "poll.vote", {"id": 1, "user_id": 1, "value": {"11": 1}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "vote/1",
            {
                "value": "Y",
                "option_id": 11,
                "weight": Decimal("3.000000"),
                "meeting_id": 113,
                "user_id": 1,
            },
        )
        self.assert_model_exists(
            "option/11",
            {
                "vote_ids": [1],
                "yes": Decimal("3.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "user/1",
            {"poll_voted_ids": [1], "delegated_vote_ids": [1], "vote_ids": [1]},
        )

    def test_vote_weight_not_enabled(self) -> None:
        self.set_models(
            {
                "group/113": {"meeting_user_ids": [11], "poll_ids": [1]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "user/1": {"default_vote_weight": Decimal("3.000000")},
                "meeting_user/11": {
                    "meeting_id": 113,
                    "user_id": 1,
                    "vote_weight": Decimal("4.200000"),
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "state": Poll.STATE_CREATED,
                    "max_votes_per_option": 1,
                    "backend": "fast",
                    "type": "named",
                    "onehundred_percent_base": "Y",
                },
                "meeting/113": {
                    "users_enable_vote_weight": False,
                    "present_user_ids": [1],
                },
            }
        )
        response = self.request(
            "poll.vote", {"id": 1, "user_id": 1, "value": {"11": 1}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "vote/1",
            {
                "value": "Y",
                "option_id": 11,
                "weight": Decimal("1.000000"),
                "meeting_id": 113,
                "user_id": 1,
            },
        )
        self.assert_model_exists(
            "option/11",
            {
                "vote_ids": [1],
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "user/1",
            {"poll_voted_ids": [1], "delegated_vote_ids": [1], "vote_ids": [1]},
        )


class VotePollBaseTestClass(BaseVoteTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(113)
        self.create_assignment(1, 113, {"open_posts": 1})
        self.create_poll()
        self.set_models(
            {
                "meeting/113": {"present_user_ids": [1]},
                "group/113": {"meeting_user_ids": [11], "poll_ids": [1]},
                "option/1": {
                    "meeting_id": 113,
                    "poll_id": 1,
                    "yes": Decimal("0.000000"),
                    "no": Decimal("0.000000"),
                    "abstain": Decimal("0.000000"),
                },
                "option/2": {
                    "meeting_id": 113,
                    "poll_id": 1,
                    "yes": Decimal("0.000000"),
                    "no": Decimal("0.000000"),
                    "abstain": Decimal("0.000000"),
                },
                "meeting_user/11": {"user_id": 1, "meeting_id": 113},
                "option/11": {"meeting_id": 113},
                "poll/1": {"global_option_id": 11},
            }
        )

    def create_poll(self) -> None:
        # has to be implemented by subclasses
        raise NotImplementedError()

    def start_poll(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_CREATED})

    def add_option(self) -> None:
        self.set_models(
            {
                "option/3": {"meeting_id": 113, "poll_id": 1},
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
                "votescast": Decimal("0.000000"),
                "votesvalid": Decimal("0.000000"),
                "votesinvalid": Decimal("0.000000"),
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
                "onehundred_percent_base": "YNA",
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
        self.assert_model_exists(
            "poll/1",
            {
                "votesvalid": Decimal("1.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("1.000000"),
                "voted_ids": [1],
            },
        )
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/3",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("1.000000"),
            },
        )

    def test_vote_with_voteweight(self) -> None:
        self.set_models(
            {
                "meeting_user/11": {"vote_weight": "4.200000"},
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
        self.assert_model_exists(
            "poll/1",
            {
                "votesvalid": Decimal("4.200000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("1.000000"),
                "state": Poll.STATE_FINISHED,
            },
        )
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("4.200000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("4.200000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/3",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("4.200000"),
            },
        )

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(response, 200)
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
        self.update_model("meeting/113", {"present_user_ids": None})
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
                "votesinvalid": Decimal("0.000000"),
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
                "onehundred_percent_base": "Y",
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
        self.assert_model_exists(
            "poll/1",
            {
                "votesvalid": Decimal("1.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("1.000000"),
                "voted_ids": [1],
            },
        )
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(response, 200)
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

    def test_global_yes(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "option/11",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

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
        self.assert_model_exists(
            "option/11",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

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
        self.assert_model_exists(
            "option/11",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("1.000000"),
            },
        )

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
        self.update_model("meeting/113", {"present_user_ids": None})
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


class VotePollYMaxVotesPerOption(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_Zrvh146QAASDfVeidq7t6iSDwZk",
                "pollmethod": "Y",
                "type": Poll.TYPE_NAMED,
                "state": Poll.STATE_CREATED,
                "meeting_id": 113,
                "votesinvalid": Decimal("0.000000"),
                "global_yes": False,
                "global_no": False,
                "global_abstain": False,
                "min_votes_amount": 1,
                "max_votes_amount": 5,
                "max_votes_per_option": 3,
                "onehundred_percent_base": "Y",
            },
        )

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 2, "2": 3}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_exists(
            "poll/1",
            {
                "votesvalid": Decimal("1.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("1.000000"),
                "voted_ids": [1],
            },
        )
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("2.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("3.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 3}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 2, "2": 0}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("3.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

    def test_vote_weight(self) -> None:
        self.update_model("user/1", {"default_vote_weight": Decimal("3.000000")})
        self.update_model("meeting/113", {"users_enable_vote_weight": True})
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 3}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("3.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("9.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

    def test_vote_change_weight(self) -> None:
        self.update_model("user/1", {"default_vote_weight": Decimal("3.000000")})
        self.update_model("meeting/113", {"users_enable_vote_weight": True})
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 2, "2": 0}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 3}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("6.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )


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
                "votesinvalid": Decimal("0.000000"),
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
                "onehundred_percent_base": "Y",
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
        self.assert_model_exists(
            "poll/1",
            {
                "votesvalid": Decimal("1.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("1.000000"),
                "voted_ids": [1],
            },
        )
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

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
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

    def test_global_yes(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "option/11",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

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
        self.assert_model_exists(
            "option/11",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

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
        self.assert_model_exists(
            "option/11",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("1.000000"),
            },
        )

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
        self.update_model("meeting/113", {"present_user_ids": None})
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
                "votesinvalid": Decimal("0.000000"),
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
                "onehundred_percent_base": "Y",
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
        self.assert_model_exists(
            "poll/1",
            {
                "votesvalid": Decimal("1.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("1.000000"),
            },
        )
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/3",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("1.000000"),
            },
        )

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
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

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
        self.update_model("meeting/113", {"present_user_ids": None})
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
                "votesinvalid": Decimal("0.000000"),
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
                "onehundred_percent_base": "Y",
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
        self.assert_model_exists(
            "poll/1",
            {
                "votesvalid": Decimal("1.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("1.000000"),
                "voted_ids": [1],
            },
        )
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists("vote/1", {"user_id": None})

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
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("1.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

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
        self.update_model("meeting/113", {"present_user_ids": None})
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


class VotePollPseudoanonymousN(VotePollBaseTestClass):
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
                "votesinvalid": Decimal("0.000000"),
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
                "onehundred_percent_base": "Y",
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
        self.assert_model_exists(
            "poll/1",
            {
                "votesvalid": Decimal("1.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votescast": Decimal("1.000000"),
                "voted_ids": [1],
            },
        )
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists("vote/1", {"user_id": None})

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
        self.assert_model_exists(
            "option/1",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("1.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

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
        self.update_model("meeting/113", {"present_user_ids": None})

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
