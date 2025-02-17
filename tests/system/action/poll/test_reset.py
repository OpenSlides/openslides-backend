from typing import Any

from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from tests.system.util import CountDatastoreCalls, Profiler, performance

from .base_poll_test import BasePollTestCase
from .poll_test_mixin import PollTestMixin


class PollResetActionTest(PollTestMixin, BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "topic/1": {
                "meeting_id": 1,
            },
            "poll/1": {
                "state": Poll.STATE_STARTED,
                "option_ids": [1],
                "global_option_id": 2,
                "meeting_id": 1,
                "content_object_id": "topic/1",
            },
            "option/1": {"vote_ids": [1, 2], "poll_id": 1, "meeting_id": 1},
            "option/2": {
                "vote_ids": [3],
                "used_as_global_option_in_poll_id": 1,
                "meeting_id": 1,
            },
            "vote/1": {"option_id": 1, "meeting_id": 1},
            "vote/2": {"option_id": 1, "meeting_id": 1},
            "vote/3": {"option_id": 2, "meeting_id": 1},
            "meeting/1": {"is_active_in_organization_id": 1},
        }

    def test_reset_correct(self) -> None:
        self.test_models["poll/1"] = {
            **self.test_models["poll/1"],
            "votesvalid": "3.000000",
            "votesinvalid": "1.000000",
            "votescast": "5.000000",
            "entitled_users_at_stop": [{"user_id": 1, "voted": True}],
        }
        self.set_models(self.test_models)

        response = self.request("poll.reset", {"id": 1})
        self.assert_status_code(response, 200)

        # check if the state has been changed to 1 (Created).
        poll = self.get_model("poll/1")
        assert poll.get("state") == "created"

        # check if not is_pseudoanonymized
        assert poll.get("is_pseudoanonymized") is False

        # check if voted_ids is cleared
        assert poll.get("voted_ids") == []

        # check if auto generated fields are cleared
        assert poll.get("entitled_users_at_stop") is None
        assert poll.get("votesvalid") is None
        assert poll.get("votesinvalid") is None
        assert poll.get("votescast") is None

        # check if the votes are deleted
        self.assert_model_deleted("vote/1")
        self.assert_model_deleted("vote/2")
        self.assert_model_deleted("vote/3")

        # check if the option.vote_ids fields are cleared
        option_1 = self.get_model("option/1")
        assert option_1.get("vote_ids") == []
        assert option_1.get("yes") == "0.000000"
        assert option_1.get("no") == "0.000000"
        assert option_1.get("abstain") == "0.000000"
        option_2 = self.get_model("option/2")
        assert option_2.get("vote_ids") == []
        assert option_2.get("yes") == "0.000000"
        assert option_2.get("no") == "0.000000"
        assert option_2.get("abstain") == "0.000000"

        # test history
        self.assert_history_information("topic/1", ["Voting reset"])

    def test_reset_assignment(self) -> None:
        self.test_models["poll/1"]["content_object_id"] = "assignment/1"
        self.test_models["assignment/1"] = {
            "meeting_id": 1,
        }
        self.set_models(self.test_models)
        response = self.request("poll.reset", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", ["Ballot reset"])

    def test_reset_no_permissions(self) -> None:
        self.base_permission_test(self.test_models, "poll.reset", {"id": 1})

    def test_reset_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "poll.reset",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_reset_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.test_models,
            "poll.reset",
            {"id": 1},
        )

    def test_reset_not_allowed_to_vote_again(self) -> None:
        self.set_models(self.test_models)
        self.set_models(
            {
                "group/1": {"meeting_user_ids": [1]},
                "user/1": {"meeting_user_ids": [1], "is_present_in_meeting_ids": [1]},
                "meeting_user/1": {"meeting_id": 1, "user_id": 1, "group_ids": [1]},
                "poll/1": {
                    "state": "started",
                    "option_ids": [1],
                    "global_option_id": 2,
                    "meeting_id": 1,
                    "entitled_group_ids": [1],
                    "pollmethod": "Y",
                    "max_votes_per_option": 1,
                    "type": "named",
                    "backend": "long",
                    "sequential_number": 1,
                    "title": "Poll 1",
                    "onehundred_percent_base": "Y",
                    "content_object_id": "topic/1",
                },
                "topic/1": {"meeting_id": 1, "poll_ids": [1], "title": "Tim the topic"},
            }
        )
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
