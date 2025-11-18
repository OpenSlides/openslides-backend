from decimal import Decimal
from typing import Any

from psycopg.types.json import Jsonb

from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from tests.system.util import CountDatastoreCalls, Profiler, performance

from .base_poll_test import BasePollTestCase
from .poll_test_mixin import PollTestMixin


class PollResetActionTest(PollTestMixin, BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.test_models: dict[str, dict[str, Any]] = {
            "poll/1": {
                "title": "Poll 1",
                "pollmethod": "YNA",
                "type": Poll.TYPE_NAMED,
                "onehundred_percent_base": Poll.ONEHUNDRED_PERCENT_BASE_YN,
                "state": Poll.STATE_STARTED,
                "global_option_id": 2,
                "meeting_id": 1,
                "content_object_id": "topic/1",
            },
            "option/1": {"poll_id": 1, "meeting_id": 1},
            "option/2": {"meeting_id": 1},
            "vote/1": {"option_id": 1, "meeting_id": 1, "user_token": "abs"},
            "vote/2": {"option_id": 1, "meeting_id": 1, "user_token": "def"},
            "vote/3": {"option_id": 2, "meeting_id": 1, "user_token": "ghi"},
        }

    def test_reset_correct(self) -> None:
        self.create_topic(1, 1)
        self.test_models["poll/1"].update(
            {
                "votesvalid": "3.000000",
                "votesinvalid": "1.000000",
                "votescast": "5.000000",
                "entitled_users_at_stop": Jsonb([{"user_id": 1, "voted": True}]),
            }
        )
        self.set_models(self.test_models)

        response = self.request("poll.reset", {"id": 1})
        self.assert_status_code(response, 200)

        # check if the state has been changed to 1 (Created).
        poll = self.get_model("poll/1")
        assert poll.get("state") == "created"

        # check if not is_pseudoanonymized
        assert poll.get("is_pseudoanonymized") is False

        # check if voted_ids is cleared
        assert poll.get("voted_ids") is None

        # check if auto generated fields are cleared
        assert poll.get("entitled_users_at_stop") is None
        assert poll.get("votesvalid") is None
        assert poll.get("votesinvalid") is None
        assert poll.get("votescast") is None

        # check if the votes are deleted
        self.assert_model_not_exists("vote/1")
        self.assert_model_not_exists("vote/2")
        self.assert_model_not_exists("vote/3")

        # check if the option.vote_ids fields are cleared
        self.assert_model_exists(
            "option/1",
            {
                "vote_ids": None,
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "vote_ids": None,
                "yes": Decimal("0.000000"),
                "no": Decimal("0.000000"),
                "abstain": Decimal("0.000000"),
            },
        )

        # test history
        self.assert_history_information("topic/1", ["Voting reset"])

    def test_reset_assignment(self) -> None:
        self.create_assignment(1, 1)
        self.test_models["poll/1"]["content_object_id"] = "assignment/1"
        self.set_models(self.test_models)
        response = self.request("poll.reset", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", ["Ballot reset"])

    def test_reset_no_permissions(self) -> None:
        self.create_topic(1, 1)
        self.base_permission_test(self.test_models, "poll.reset", {"id": 1})

    def test_reset_permissions(self) -> None:
        self.create_topic(1, 1)
        self.base_permission_test(
            self.test_models,
            "poll.reset",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_reset_permissions_locked_meeting(self) -> None:
        self.create_topic(1, 1)
        self.base_locked_out_superadmin_permission_test(
            self.test_models,
            "poll.reset",
            {"id": 1},
        )

    def test_reset_not_allowed_to_vote_again(self) -> None:
        self.create_topic(1, 1)
        self.test_models["poll/1"].update(
            {
                "pollmethod": "Y",
                "max_votes_per_option": 1,
                "backend": "long",
                "onehundred_percent_base": "Y",
            }
        )
        self.test_models["group/1"] = {"poll_ids": [1]}
        self.set_models(self.test_models)
        self.set_user_groups(1, [1])
        self.vote_service.start(1)
        response = self.vote_service.vote({"id": 1, "value": {"1": 1}})
        self.assert_status_code(response, 200)
        response = self.request("poll.reset", {"id": 1})
        self.assert_status_code(response, 200)
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        response = self.vote_service.vote({"id": 1, "value": {"1": 1}})
        self.assert_status_code(response, 200)

    def test_reset_datastore_calls(self) -> None:
        self.prepare_users_and_poll(3)

        with CountDatastoreCalls() as counter:
            response = self.request("poll.reset", {"id": 1})

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1", {"voted_ids": [], "state": Poll.STATE_CREATED}
        )
        assert counter.calls == 5

    @performance
    def test_reset_performance(self) -> None:
        # TODO this needs a different idea
        self.prepare_users_and_poll(100)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        self.datastore.reset(hard=True)

        with Profiler("test_reset_performance.prof"):
            response = self.request("poll.reset", {"id": 1})

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1", {"voted_ids": [], "state": Poll.STATE_CREATED}
        )
