from typing import Any, cast

import pytest
import requests
import simplejson as json

from openslides_backend.models.models import Poll
from openslides_backend.shared.exceptions import ActionException
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.util import convert_to_test_response
from tests.util import Response

from .base_poll_test import BasePollTestCase


class BaseVoteTestCase(BasePollTestCase):
    def request_tuple_response(
        self,
        action: str,
        data: dict[str, Any],
        anonymous: bool = False,
        lang: str | None = None,
        internal: bool | None = None,
        start_poll_before_vote: bool = True,
        stop_poll_after_vote: bool = True,
    ) -> tuple[Response, Response | None]:
        """Overwrite request method to reroute voting requests to the vote service."""
        if action == "poll.vote":
            if start_poll_before_vote:
                self.execute_action_internally("poll.start", {"id": data["id"]})
            response = self.vote_service.vote(data)
            stop_response = None
            if stop_poll_after_vote:
                stop_response = super().request(
                    "poll.stop", {"id": data["id"]}, anonymous, lang
                )
            return (response, stop_response)
        else:
            return (super().request(action, data, anonymous, lang, internal), None)

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
        self.create_model(
            "meeting/113",
            {"is_active_in_organization_id": 1},
        )

    def test_vote_correct_pollmethod_Y(self) -> None:
        user_id = self.create_user("test2")
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {
                    "meeting_user_ids": [11, 12],
                    "poll_ids": [1],
                    "permissions": ["motion.can_manage_polls"],
                },
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                    "meeting_ids": [113],
                },
                "meeting_user/11": {
                    "meeting_id": 113,
                    "user_id": 1,
                    "group_ids": [1],
                },
                f"user/{user_id}": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [12],
                    "meeting_ids": [113],
                },
                "meeting_user/12": {
                    "meeting_id": 113,
                    "user_id": user_id,
                    "vote_weight": "2.000000",
                    "group_ids": [1],
                },
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "option_ids": [11],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 10,
                    "max_votes_per_option": 1,
                    "backend": Poll.BACKEND_FAST,
                },
                "meeting/113": {
                    "users_enable_vote_weight": True,
                    "meeting_user_ids": [11, 12],
                },
            }
        )
        vote_response, _ = self.request_tuple_response(
            "poll.vote", {"id": 1, "value": {"11": 1}}, stop_poll_after_vote=False
        )
        self.assert_status_code(vote_response, 200)
        self.login(user_id)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"id": 1, "value": {"11": 1}}, start_poll_before_vote=False
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

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
            assert vote.get("weight") == f"{user_id}.000000"
        self.assert_model_exists(
            "option/11",
            {
                "vote_ids": [1, 2],
                "yes": "3.000000",
                "no": "0.000000",
                "abstain": "0.000000",
            },
        )

    def test_value_check(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "YN",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "backend": Poll.BACKEND_FAST,
                    "type": Poll.TYPE_NAMED,
                    "state": Poll.STATE_CREATED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"11": "Y", "12": "N", "13": "A"},
            },
        )
        self.assert_status_code(vote_response, 400)
        assert (
            "Data for option 13 does not fit the poll method."
            in vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

    def test_vote_correct_pollmethod_YN(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "YN",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 10,
                    "max_votes_per_option": 1,
                    "backend": Poll.BACKEND_FAST,
                    "type": Poll.TYPE_NAMED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"11": "Y", "12": "N"},
            },
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        vote = self.assert_model_exists(
            "vote/1",
            {
                "value": "Y",
                "option_id": 11,
                "weight": "1.000000",
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
                "weight": "1.000000",
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
                "yes": "1.000000",
                "no": "0.000000",
                "abstain": "0.000000",
            },
        )
        self.assert_model_exists(
            "option/12",
            {
                "vote_ids": [2],
                "yes": "0.000000",
                "no": "1.000000",
                "abstain": "0.000000",
            },
        )

    def test_vote_wrong_votes_total(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_option": 1,
                    "backend": Poll.BACKEND_FAST,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"11": 1, "12": 1},
            },
        )
        self.assert_status_code(vote_response, 400)
        assert (
            "The sum of your answers has to be between 1 and 1"
            in vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_vote_pollmethod_Y_wrong_value(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "backend": Poll.BACKEND_FAST,
                    "state": Poll.STATE_CREATED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {
                "id": 1,
                "value": {"11": "Y"},
            },
        )
        self.assert_status_code(vote_response, 400)
        assert "Your vote has a wrong format" in vote_response.json["message"]
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_vote_no_votes_total_check_by_YNA(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "YNA",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_option": 1,
                    "backend": Poll.BACKEND_FAST,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"11": "Y", "12": "A"},
            },
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_exists("vote/1")

    def test_vote_no_votes_total_check_by_YN(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "YN",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_option": 1,
                    "backend": Poll.BACKEND_FAST,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"11": "Y", "12": "N"},
            },
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_exists("vote/1")

    def test_vote_wrong_votes_total_min_case(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "option/12": {"meeting_id": 113, "poll_id": 1},
                "option/13": {"meeting_id": 113, "poll_id": 1},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "option_ids": [11, 12, 13],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "min_votes_amount": 2,
                    "max_votes_amount": 2,
                    "max_votes_per_option": 1,
                    "backend": Poll.BACKEND_FAST,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"11": 1},
            },
        )
        self.assert_status_code(vote_response, 400)
        assert (
            "The sum of your answers has to be between 2 and 2"
            in vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_vote_global(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11, 12]},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "user/2": {
                    "username": "test2",
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [12],
                },
                "meeting_user/12": {
                    "user_id": 2,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "pollmethod": "YNA",
                    "backend": Poll.BACKEND_FAST,
                },
            }
        )
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": "N"},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "user_id": 2, "value": "Y"},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Vote delegation is not activated in meeting 113",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

        self.assert_model_exists(
            "vote/1",
            {
                "value": "N",
                "option_id": 11,
                "weight": "1.000000",
                "meeting_id": 113,
                "user_id": 1,
            },
        )
        self.assert_model_exists(
            "option/11",
            {
                "vote_ids": [1],
                "yes": "0.000000",
                "no": "1.000000",
                "abstain": "0.000000",
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
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "entitled_group_ids": [1],
                    "meeting_id": 113,
                    "pollmethod": "YNA",
                    "backend": Poll.BACKEND_FAST,
                    "state": Poll.STATE_CREATED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"id": 1, "user_id": 1, "value": "X"}
        )
        self.assert_status_code(vote_response, 400)
        assert "Global vote X is not enabled" in vote_response.json["message"]
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

    def test_vote_invalid_vote_value(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "option_ids": [11],
                    "pollmethod": "YNA",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "meeting_id": 113,
                    "backend": Poll.BACKEND_FAST,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"11": "X"},
            },
        )
        self.assert_status_code(vote_response, 400)
        assert (
            "Data for option 11 does not fit the poll method."
            in vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

    def test_vote_not_started_in_service(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "type": Poll.TYPE_NAMED,
                    "meeting_id": 113,
                    "pollmethod": "YNA",
                    "global_yes": True,
                    "entitled_group_ids": [1],
                    "backend": Poll.BACKEND_FAST,
                    "state": Poll.STATE_CREATED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"id": 1, "value": "Y"},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_vote_option_not_in_poll(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "type": Poll.TYPE_NAMED,
                    "pollmethod": "YNA",
                    "entitled_group_ids": [1],
                    "meeting_id": 113,
                    "backend": Poll.BACKEND_FAST,
                    "state": Poll.STATE_CREATED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {
                "id": 1,
                "user_id": 1,
                "value": {"113": "Y"},
            },
        )
        self.assert_status_code(vote_response, 400)
        assert (
            "Option_id 113 does not belong to the poll" in vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

    def test_double_vote(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11, 12]},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "user/2": {
                    "username": "test2",
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [12],
                },
                "meeting_user/12": {
                    "user_id": 2,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "pollmethod": "YN",
                    "backend": Poll.BACKEND_FAST,
                    "state": Poll.STATE_CREATED,
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": "N"},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": "N"},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        assert "Not the first vote" in vote_response.json["message"]
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

        self.assert_model_exists(
            "vote/1",
            {
                "value": "N",
                "option_id": 11,
                "weight": "1.000000",
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
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                    "meeting_ids": [113],
                },
                "meeting_user/11": {"user_id": 1, "meeting_id": 113, "group_ids": [1]},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "pollmethod": "YNA",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "entitled_group_ids": [],
                    "backend": Poll.BACKEND_FAST,
                    "state": Poll.STATE_CREATED,
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"id": 1, "user_id": 1, "value": "N"}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "User 1 is not allowed to vote. He is not in an entitled group",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

    def test_check_user_present_in_meeting(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "user/1": {"meeting_user_ids": [11]},
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "global_option_id": 11,
                    "global_no": True,
                    "global_yes": False,
                    "global_abstain": False,
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "backend": Poll.BACKEND_FAST,
                    "pollmethod": "YNA",
                    "state": Poll.STATE_CREATED,
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"id": 1, "value": "N"}
        )
        self.assert_status_code(vote_response, 400)
        assert "You have to be present in meeting 113" in vote_response.json["message"]
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

    def test_check_str_validation(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "type": Poll.TYPE_NAMED,
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "pollmethod": "Y",
                    "backend": Poll.BACKEND_FAST,
                    "state": Poll.STATE_CREATED,
                },
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"id": 1, "user_id": 1, "value": "X"}
        )
        self.assert_status_code(vote_response, 400)
        assert "Global vote X is not enabled" in vote_response.json["message"]
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

    def test_default_vote_weight(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "meeting_user_ids": [11],
                    "default_vote_weight": "3.000000",
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "option_ids": [11],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "max_votes_per_option": 1,
                    "backend": Poll.BACKEND_FAST,
                },
                "meeting/113": {"users_enable_vote_weight": True},
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"id": 1, "user_id": 1, "value": {"11": 1}}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

        self.assert_model_exists(
            "vote/1",
            {
                "value": "Y",
                "option_id": 11,
                "weight": "3.000000",
                "meeting_id": 113,
                "user_id": 1,
            },
        )
        self.assert_model_exists(
            "option/11",
            {
                "vote_ids": [1],
                "yes": "3.000000",
                "no": "0.000000",
                "abstain": "0.000000",
            },
        )
        self.assert_model_exists(
            "user/1",
            {"poll_voted_ids": [1], "delegated_vote_ids": [1], "vote_ids": [1]},
        )

    def test_vote_weight_not_enabled(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11]},
                "option/11": {"meeting_id": 113, "poll_id": 1},
                "user/1": {
                    "is_present_in_meeting_ids": [113],
                    "default_vote_weight": "3.000000",
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "meeting_id": 113,
                    "user_id": 1,
                    "vote_weight": "4.200000",
                    "group_ids": [1],
                },
                "motion/1": {
                    "meeting_id": 113,
                },
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "motion/1",
                    "title": "my test poll",
                    "option_ids": [11],
                    "pollmethod": "Y",
                    "meeting_id": 113,
                    "entitled_group_ids": [1],
                    "state": Poll.STATE_CREATED,
                    "max_votes_per_option": 1,
                    "backend": Poll.BACKEND_FAST,
                },
                "meeting/113": {
                    "users_enable_vote_weight": False,
                    "meeting_user_ids": [11],
                },
            }
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"id": 1, "user_id": 1, "value": {"11": 1}}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

        self.assert_model_exists(
            "vote/1",
            {
                "value": "Y",
                "option_id": 11,
                "weight": "1.000000",
                "meeting_id": 113,
                "user_id": 1,
            },
        )
        self.assert_model_exists(
            "option/11",
            {
                "vote_ids": [1],
                "yes": "1.000000",
                "no": "0.000000",
                "abstain": "0.000000",
            },
        )
        self.assert_model_exists(
            "user/1",
            {"poll_voted_ids": [1], "delegated_vote_ids": [1], "vote_ids": [1]},
        )


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
                "group/1": {"meeting_user_ids": [11], "meeting_id": 113},
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
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 113,
                    "group_ids": [1],
                },
                "option/11": {"meeting_id": 113, "used_as_global_option_in_poll_id": 1},
                "poll/1": {"global_option_id": 11, "backend": Poll.BACKEND_FAST},
            }
        )

    def create_poll(self) -> None:
        # has to be implemented by subclasses
        raise NotImplementedError()

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
                "max_votes_per_option": 1,
            },
        )

    def test_vote(self) -> None:
        self.add_option()
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
                "user/1": {"meeting_user_ids": [11]},
                "meeting_user/11": {
                    "meeting_id": 113,
                    "user_id": 1,
                    "vote_weight": "4.200000",
                },
                "meeting/113": {"users_enable_vote_weight": True},
            }
        )
        self.add_option()
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "N"}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/2")
        self.assert_model_exists("vote/1", {"value": "Y"})

    def test_too_many_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Option_id 3 does not belong to the poll", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Option_id 3 does not belong to the poll", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        vote_response = self.anonymous_vote({"value": {"1": "Y"}})
        self.assert_status_code(vote_response, 401)
        self.assertIn("Anonymous user can not vote", vote_response.json["message"])
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "You have to be present in meeting 113", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"value": {"1": "Y"}, "id": 1, "user_id": 1},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": {}, "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Your vote has a wrong format",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "decoding payload: unknown vote value: `[1,2,5]`",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Data for option 1 does not fit the poll method.",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"id": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"id":"Y"}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"1":[null]}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
                "max_votes_per_option": 1,
            },
        )

    def test_vote(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

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
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_global_yes(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "Y", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )

        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "1.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "0.000000")

    def test_global_yes_forbidden(self) -> None:
        self.update_model("poll/1", {"global_yes": False})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "Y", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Global vote Y is not enabled", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_global_no(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "N", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "1.000000")
        self.assertEqual(option.get("abstain"), "0.000000")

    def test_global_no_forbidden(self) -> None:
        self.update_model("poll/1", {"global_no": False})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "N", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Global vote N is not enabled", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_global_abstain(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "A", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "1.000000")

    def test_global_abstain_forbidden(self) -> None:
        self.update_model("poll/1", {"global_abstain": False})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "A", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Global vote A is not enabled", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_negative_vote(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Your vote for option 1 has to be >= 0", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_too_many_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 1, "3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Option_id 3 does not belong to the poll", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "value": {"3": 1}},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Option_id 3 does not belong to the poll", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        vote_response = self.anonymous_vote({"value": {"1": 1}})
        self.assert_status_code(vote_response, 401)
        self.assertIn("Anonymous user can not vote", vote_response.json["message"])
        self.assert_model_not_exists("vote/1")

    def test_anonymous_as_vote_user(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 0},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Votes for anonymous user are not allowed", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        assert (
            "Votes for anonymous user are not allowed" in vote_response.json["message"]
        )
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "You have to be present in meeting 113", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"value": {"1": 1}, "id": 1, "user_id": 1},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": {}, "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "The sum of your answers has to be between 1 and 10",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "decoding payload: unknown vote value: `[1,2,5]`",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Your vote has a wrong format",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"id":1}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"1":[null]}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
                "global_yes": False,
                "global_no": False,
                "global_abstain": False,
                "min_votes_amount": 1,
                "max_votes_amount": 5,
                "max_votes_per_option": 3,
            },
        )

    def test_vote(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 2, "2": 3}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertIn(1, poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "2.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "3.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_change_vote(self) -> None:
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 3}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 2, "2": 0}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "3.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_vote_weight(self) -> None:
        self.update_model("user/1", {"default_vote_weight": "3.000000"})
        self.update_model("meeting/113", {"users_enable_vote_weight": True})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 3}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "3.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "9.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_vote_change_weight(self) -> None:
        self.update_model("user/1", {"default_vote_weight": "3.000000"})
        self.update_model("meeting/113", {"users_enable_vote_weight": True})
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 2, "2": 0}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 0, "2": 3}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "6.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")


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
                "max_votes_per_option": 1,
            },
        )

    def test_vote(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "0.000000")
        self.assertEqual(option1.get("no"), "1.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_global_yes(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "Y", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "1.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "0.000000")

    def test_global_yes_forbidden(self) -> None:
        self.update_model("poll/1", {"global_yes": False})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "Y", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Global vote Y is not enabled", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_global_no(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "N", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "1.000000")
        self.assertEqual(option.get("abstain"), "0.000000")

    def test_global_no_forbidden(self) -> None:
        self.update_model("poll/1", {"global_no": False})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "N", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Global vote N is not enabled", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_global_abstain(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "A", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "1.000000")

    def test_global_abstain_forbidden(self) -> None:
        self.update_model("poll/1", {"global_abstain": False})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": "A", "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Global vote A is not enabled", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_negative_vote(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Your vote for option 1 has to be >= 0", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Option_id 3 does not belong to the poll", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        vote_response = self.anonymous_vote({"value": {"1": 1}})
        self.assert_status_code(vote_response, 401)
        self.assertIn("Anonymous user can not vote", vote_response.json["message"])
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "You have to be present in meeting 113", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"value": {"1": 1}, "id": 1, "user_id": 1},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": {}, "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "The sum of your answers has to be between 1 and 10",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "decoding payload: unknown vote value: `[1,2,5]`",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Your vote has a wrong format",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"id":1}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"1":[null]}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
                "max_votes_per_option": 1,
            },
        )

    def test_vote(self) -> None:
        self.add_option()
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "N"}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option1 = self.get_model("option/1")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")

    def test_too_many_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Option_id 3 does not belong to the poll", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_partial_vote(self) -> None:
        self.add_option()
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_exists("vote/1")

    def test_wrong_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Option_id 3 does not belong to the poll", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        vote_response = self.anonymous_vote({"value": {"1": "Y"}})
        self.assert_status_code(vote_response, 401)
        self.assertIn("Anonymous user can not vote", vote_response.json["message"])
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "You have to be present in meeting 113", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"value": {}, "id": 1, "user_id": 1},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_missing_value(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": {}, "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Your vote has a wrong format",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_value_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "decoding payload: unknown vote value: `[1,2,5]`",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Data for option 1 does not fit the poll method.",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"id": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"id":"Y"}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_value(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"1":[null]}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
                "max_votes_per_option": 1,
            },
        )

    def test_vote(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Your vote for option 1 has to be >= 0", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Option_id 3 does not belong to the poll", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "You have to be present in meeting 113", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"value": {"1": 1}, "id": 1, "user_id": 1},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": {}, "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "The sum of your answers has to be between 1 and 10",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"value": [1, 2, 5]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"value":[1,2,5]}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Your vote has a wrong format",
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"id":1}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            'decoding payload: unknown vote value: `{"1":[null]}`',
            vote_response.json["message"],
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
            },
        )

    def test_vote(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "value": {"1": 1, "2": 0}, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_exists("vote/1", {"user_id": None})
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
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "Your vote for option 1 has to be >= 0", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.update_model("user/1", {"is_present_in_meeting_ids": []})

        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": {"1": 1}},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "You have to be present in meeting 113", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"value": {"1": 1}, "id": 1, "user_id": 1},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_wrong_data_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        assert (
            "decoding payload: unknown vote value: `[1,2,5]`"
            in vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        assert "Your vote has a wrong format" in vote_response.json["message"]
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("decoding payload: EOF", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "value": {"1": [None]}, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        assert "decoding payload: unknown vote value:" in vote_response.json["message"]
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")


class VotePollCryptographicYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_OkHAIvOSIcpFnCxbaL6v",
                "pollmethod": "YNA",
                "type": Poll.TYPE_CRYPTOGRAPHIC,
                "state": Poll.STATE_CREATED,
                "backend": Poll.BACKEND_FAST,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
            },
        )

    def test_vote(self) -> None:
        self.add_option()
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "N"}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        option1 = self.get_model("option/1")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")

    def test_too_many_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn("Option_id 3 does not belong to the poll", vote["msg"])

        self.assert_model_not_exists("vote/1")

    def test_partial_vote(self) -> None:
        self.add_option()
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_exists("vote/1")

    def test_wrong_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn("Option_id 3 does not belong to the poll", vote["msg"])
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        vote_response = self.anonymous_vote({"value": {"1": "Y"}})
        self.assert_status_code(vote_response, 401)
        self.assertIn("Anonymous user can not vote", vote_response.json["message"])
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "You have to be present in meeting 113", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"value": {}, "id": 1, "user_id": 1},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_missing_value(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": {}, "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn("Your vote has a wrong format", vote["msg"])
        self.assert_model_not_exists("vote/1")
        self.assert_model_exists(
            "poll/1",
            {
                "votesvalid": "0.000000",
                "votesinvalid": "1.000000",
                "votescast": "1.000000",
                "voted_ids": [1],
            },
        )

    def test_wrong_value_format_REPORT(self) -> None:
        """
        Should give the error for the one vote in poll.stop, but not kill the whole poll:
        vote_service log: Error: encoding decrypted votes: unknown vote value: `[1,2,5]`
        Error poll_stop: Vote service sends HTTP 500 Internal Server Error.
        """
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 400)
        self.assertIn(
            "Vote service sends HTTP 500 Internal Server Error.",
            cast(Response, stop_response).json["message"],
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn(
                "Data for option 1 does not fit the poll method.", vote["msg"]
            )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type_REPORT(self) -> None:
        """
        vote-service log: encoding decrypted votes: unknown vote value: `{"id":"Y"}`,
        but kills the whole poll with "Vote service sends HTTP 500 Internal Server Error.".
        """
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"id": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 400)
        self.assertIn(
            "Vote service sends HTTP 500 Internal Server Error.",
            cast(Response, stop_response).json["message"],
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_value_REPORT(self) -> None:
        """
        Should give the error for the one vote in poll.stop, but not kill the whole poll:
        Log Message vote-service: decrypting votes: sending grpc message: rpc error: code = Internal desc = Ups, someting went wrong!
        Error message stop_response: Vote service sends HTTP 500 Internal Server Error.
        """
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 400)
        self.assertIn(
            "Vote service sends HTTP 500 Internal Server Error.",
            cast(Response, stop_response).json["message"],
        )
        self.assert_model_not_exists("vote/1")


class VotePollCryptographicY(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_Zrvh146QAdq7t6iSDwZk",
                "pollmethod": "Y",
                "type": Poll.TYPE_CRYPTOGRAPHIC,
                "state": Poll.STATE_CREATED,
                "backend": Poll.BACKEND_FAST,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
            },
        )

    def test_vote(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_exists(
            "vote/1",
            {"value": "Y", "option_id": 1},
        )
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

    def test_change_vote(self) -> None:
        vote_response, _ = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )
        self.assert_status_code(vote_response, 200)
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn("Your vote for option 1 has to be >= 0", vote["msg"])
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn("Option_id 3 does not belong to the poll", vote["msg"])
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.update_model("user/1", {"is_present_in_meeting_ids": []})
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "You have to be present in meeting 113", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"value": {"1": 1}, "id": 1, "user_id": 1},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote", {"value": {}, "id": 1, "user_id": 1}
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn(
                "The sum of your answers has to be between 1 and 10", vote["msg"]
            )
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertIn(1, poll.get("voted_ids", []))
        assert poll.get("votesvalid") == "0.000000"
        assert poll.get("votesinvalid") == "1.000000"

    def test_wrong_data_format_REPORT(self) -> None:
        """
        Should give the error for the one vote in poll.stop, but not kill the whole poll:
        Vote-Service-Log: encoding decrypted votes: unknown vote value: `{"value":[1,2,5]}`
        """
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"value": [1, 2, 5]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 400)
        self.assertIn(
            "Vote service sends HTTP 500 Internal Server Error.",
            cast(Response, stop_response).json["message"],
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn("Your vote has a wrong format", vote["msg"])
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type_REPORT(self) -> None:
        """
        vote-service log-message: encoding decrypted votes: unknown vote value: `{"id":1}`
        Will be replaced in vote adapter thru 'Vote service sends HTTP 500 Internal Server Error.'
        """
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 400)
        self.assertIn(
            "Vote service sends HTTP 500 Internal Server Error.",
            cast(Response, stop_response).json["message"],
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data_REPORT(self) -> None:
        """
        vote-service-log: decrypting votes: sending grpc message: rpc error: code = Internal desc = Ups, someting went wrong!
        shouldn't kill the whole poll.stop, instead give an error just for the one vote
        """
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 400)
        self.assertIn(
            "Vote service sends HTTP 500 Internal Server Error.",
            cast(Response, stop_response).json["message"],
        )
        self.assert_model_not_exists("vote/1")


class VotePollCryptographicN(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_wWPOVJgL9afm83eamf3e",
                "pollmethod": "N",
                "type": Poll.TYPE_CRYPTOGRAPHIC,
                "state": Poll.STATE_CREATED,
                "backend": Poll.BACKEND_FAST,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
                "votesinvalid": "0.000000",
                "min_votes_amount": 1,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
            },
        )

    def test_vote(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "value": {"1": 1, "2": 0}, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_exists(
            "vote/1",
            {"value": "N", "option_id": 1},
        )
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

    def test_change_vote_REPORT(self) -> None:
        """typo in message: Should be double instead douple"""
        self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
            stop_poll_after_vote=False,
        )

        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
            start_poll_before_vote=False,
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn("Not the first vote", vote_response.json["message"])
        self.assertIn("double-vote", vote_response.json["error"])
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
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
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        self.assert_model_not_exists("vote/1")
        self.assertIn(
            "Actions handled successfully",
            cast(Response, stop_response).json["message"],
        )
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn("Your vote for option 1 has to be >= 0", vote["msg"])

    def test_vote_not_present(self) -> None:
        self.update_model("user/1", {"is_present_in_meeting_ids": []})

        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": {"1": 1}},
        )
        self.assert_status_code(vote_response, 400)
        self.assertIn(
            "You have to be present in meeting 113", vote_response.json["message"]
        )
        self.assert_status_code(cast(Response, stop_response), 200)
        assert (
            cast(Response, stop_response).json["results"][0][0]["invalid_votes"] == []
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        with pytest.raises(ActionException) as e:
            self.request_tuple_response(
                "poll.vote",
                {"value": {"1": 1}, "id": 1, "user_id": 1},
                start_poll_before_vote=False,
                stop_poll_after_vote=False,
            )
        self.assertIn("Backendtest: Poll not started!", e.value.message)
        self.assert_model_not_exists("vote/1")

    def test_wrong_data_format_REPORT(self) -> None:
        """ """
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 400)
        self.assertIn(
            "Vote service sends HTTP 500 Internal Server Error.",
            cast(Response, stop_response).json["message"],
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 200)
        self.assert_model_not_exists("vote/1")
        self.assertIn(
            "Actions handled successfully",
            cast(Response, stop_response).json["message"],
        )
        invalid_votes = cast(Response, stop_response).json["results"][0][0][
            "invalid_votes"
        ]
        for vote in invalid_votes:
            self.assertIn("Your vote has a wrong format", vote["msg"])

    def test_wrong_option_id_type_REPORT(self) -> None:
        """
        vote-service log: decrypting votes: sending grpc message: rpc error: code = Internal desc = Ups, someting went wrong!
        shouldn't kill the whole poll.stop
        """
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 400)
        self.assertIn(
            "Vote service sends HTTP 500 Internal Server Error.",
            cast(Response, stop_response).json["message"],
        )
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data_REPORT(self) -> None:
        """
        vote-service log: decrypting votes: sending grpc message: rpc error: code = Internal desc = Ups, someting went wrong!
        shouldn't kill the whole poll.stop
        """
        vote_response, stop_response = self.request_tuple_response(
            "poll.vote",
            {"id": 1, "value": {"1": [None]}, "user_id": 1},
        )
        self.assert_status_code(vote_response, 200)
        self.assert_status_code(cast(Response, stop_response), 400)
        self.assertIn(
            "Vote service sends HTTP 500 Internal Server Error.",
            cast(Response, stop_response).json["message"],
        )
        self.assert_model_not_exists("vote/1")
