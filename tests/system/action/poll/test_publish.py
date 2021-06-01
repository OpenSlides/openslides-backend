from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class PollPublishActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "poll/1": {"state": "finished", "meeting_id": 1},
        }

    def test_publish_correct(self) -> None:
        self.set_models(
            {
                "poll/1": {"state": "finished", "meeting_id": 1},
                "meeting/1": {},
            }
        )
        response = self.request("poll.publish", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "published"

    def test_publish_wrong_state(self) -> None:
        self.set_models(
            {
                "poll/1": {"state": "created", "meeting_id": 1},
                "meeting/1": {},
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
        self.set_models(
            {
                "poll/1": {"state": "started", "meeting_id": 1},
                "meeting/1": {},
            }
        )
        response = self.request("poll.publish", {"id": 1})    
        self.assert_status_code(response, 200)
        self.assert_model_exists("poll/1",
            {
                "votescast": "0.000000",
                "votesinvalid": "0.000000",
                "votesvalid": "0.000000",
                "entitled_users_at_stop": [],
                })

    def test_publish_no_permissions(self) -> None:
        self.base_permission_test(self.permission_test_model, "poll.publish", {"id": 1})

    def test_publish_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "poll.publish",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )
