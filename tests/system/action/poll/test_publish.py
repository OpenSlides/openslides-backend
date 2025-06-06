from typing import Any

from openslides_backend.permissions.permissions import Permissions

from .base_poll_test import BasePollTestCase


class PollPublishActionTest(BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "poll/1": {
                "type": "named",
                "pollmethod": "Y",
                "backend": "long",
                "state": "finished",
                "meeting_id": 1,
                "content_object_id": "topic/1",
                "sequential_number": 1,
                "title": "Poll 1",
                "onehundred_percent_base": "YNA",
            },
            "topic/1": {"meeting_id": 1},
            "committee/1": {"meeting_ids": [1]},
            "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
        }

    def test_publish_correct(self) -> None:
        self.set_models(self.test_models)
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "published"
        self.assert_history_information("topic/1", ["Voting published"])

    def test_publish_assignment(self) -> None:
        self.test_models["poll/1"]["content_object_id"] = "assignment/1"
        self.test_models["assignment/1"] = {
            "meeting_id": 1,
        }
        self.set_models(self.test_models)
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", ["Ballot published"])

    def test_publish_wrong_state(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "topic/1": {"poll_ids": [111], "meeting_id": 1},
                "poll/1": {
                    "state": "created",
                    "meeting_id": 1,
                    "content_object_id": "topic/1",
                },
                "meeting/1": {"topic_ids": [1]},
            }
        )
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "created"
        assert (
            "Cannot publish poll 1, because it is not in state finished or started."
            in response.json["message"]
        )

    def test_publish_started(self) -> None:
        self.test_models["poll/1"]["state"] = "started"
        self.set_models(self.test_models)
        self.vote_service.start(1)
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "votescast": "0.000000",
                "votesinvalid": "0.000000",
                "votesvalid": "0.000000",
                "entitled_users_at_stop": [],
            },
        )
        self.assert_history_information("topic/1", ["Voting stopped/published"])

    def test_publish_no_permissions(self) -> None:
        self.base_permission_test(self.test_models, "poll.publish", {"id": 1})

    def test_publish_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "poll.publish",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_publish_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.test_models,
            "poll.publish",
            {"id": 1},
        )
