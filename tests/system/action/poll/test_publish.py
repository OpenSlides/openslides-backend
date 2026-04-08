from decimal import Decimal
from typing import Any

from openslides_backend.permissions.permissions import Permissions

from .base_poll_test import BasePollTestCase


class PollPublishActionTest(BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_topic(1, 1)
        self.poll_data: dict[str, dict[str, Any]] = {
            "poll/1": {
                "type": "named",
                "pollmethod": "Y",
                "backend": "long",
                "state": "finished",
                "meeting_id": 1,
                "content_object_id": "topic/1",
                "title": "Poll 1",
                "onehundred_percent_base": "YNA",
            },
        }

    def test_publish_correct(self) -> None:
        self.set_models(self.poll_data)
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "published"
        self.assert_history_information("topic/1", None)

    def test_publish_motion(self) -> None:
        self.create_motion(1, 2)
        self.poll_data["poll/1"]["content_object_id"] = "motion/2"
        self.set_models(self.poll_data)
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/2", ["Voting published"])

    def test_publish_assignment(self) -> None:
        self.create_assignment(1, 1)
        self.poll_data["poll/1"]["content_object_id"] = "assignment/1"
        self.set_models(self.poll_data)
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", ["Ballot published"])

    def test_publish_wrong_state(self) -> None:
        self.poll_data["poll/1"]["state"] = "created"
        self.set_models(self.poll_data)
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "created"
        self.assertEqual(
            "Cannot publish poll 1, because it is not in state finished or started.",
            response.json["message"],
        )

    def test_publish_started(self) -> None:
        self.create_motion(1, 2)
        self.poll_data["poll/1"]["content_object_id"] = "motion/2"
        self.poll_data["poll/1"]["state"] = "started"
        self.set_models(self.poll_data)
        self.vote_service.start(1)
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "votescast": Decimal("0.000000"),
                "votesinvalid": Decimal("0.000000"),
                "votesvalid": Decimal("0.000000"),
                "entitled_users_at_stop": [],
            },
        )
        self.assert_history_information("motion/2", ["Voting stopped/published"])

    def test_publish_no_permissions(self) -> None:
        self.base_permission_test(self.poll_data, "poll.publish", {"id": 1})

    def test_publish_permissions(self) -> None:
        self.base_permission_test(
            self.poll_data,
            "poll.publish",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_publish_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.poll_data,
            "poll.publish",
            {"id": 1},
        )
