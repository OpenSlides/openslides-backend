from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class PollStopActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "poll/1": {"state": "started", "meeting_id": 1},
            "meeting/1": {"poll_couple_countdown": True, "poll_countdown_id": 1},
            "projector_countdown/1": {
                "running": True,
                "default_time": 60,
                "countdown_time": 30.0,
            },
        }

    def test_stop_correct(self) -> None:
        self.set_models(
            {
                "poll/1": {"state": "started", "meeting_id": 1},
                "meeting/1": {"poll_couple_countdown": True, "poll_countdown_id": 1},
                "projector_countdown/1": {
                    "running": True,
                    "default_time": 60,
                    "countdown_time": 30.0,
                },
            }
        )
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "finished"
        countdown = self.get_model("projector_countdown/1")
        assert countdown.get("running") is False
        assert countdown.get("countdown_time") == 60

    def test_stop_wrong_state(self) -> None:
        self.set_models(
            {
                "poll/1": {"state": "published", "meeting_id": 1},
                "meeting/1": {},
            }
        )
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "published"
        assert (
            "Cannot stop poll 1, because it is not in state started."
            in response.json["message"]
        )

    def test_stop_no_permissions(self) -> None:
        self.base_permission_test(self.permission_test_model, "poll.stop", {"id": 1})

    def test_stop_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "poll.stop",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )
