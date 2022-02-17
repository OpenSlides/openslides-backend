from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class PollStopActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models = {
            "poll/1": {"state": Poll.STATE_STARTED, "meeting_id": 1},
            "meeting/1": {"is_active_in_organization_id": 1},
        }

    def start_poll(self, id: int) -> None:
        self.vote_service.start(id)

    def test_stop_correct(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_electronic_voting": True},
                "poll/1": {
                    "type": Poll.TYPE_NAMED,
                    "pollmethod": "YN",
                    "state": Poll.STATE_STARTED,
                    "option_ids": [1],
                    "meeting_id": 1,
                    "entitled_group_ids": [1],
                },
                "option/1": {"meeting_id": 1, "poll_id": 1},
                "group/1": {"meeting_id": 1},
                "meeting/1": {
                    "users_enable_vote_weight": True,
                    "default_group_id": 1,
                    "poll_couple_countdown": True,
                    "poll_countdown_id": 1,
                    "is_active_in_organization_id": 1,
                    "group_ids": [1],
                },
                "projector_countdown/1": {
                    "running": True,
                    "default_time": 60,
                    "countdown_time": 30.0,
                    "meeting_id": 1,
                },
            }
        )
        user1 = self.create_user_for_meeting(1)
        user2 = self.create_user_for_meeting(1)
        user3 = self.create_user_for_meeting(1)
        self.set_models(
            {
                f"user/{user1}": {
                    "vote_weight_$1": "2.000000",
                    "is_present_in_meeting_ids": [1],
                },
                f"user/{user2}": {
                    "vote_weight_$1": "3.000000",
                    "is_present_in_meeting_ids": [1],
                },
                f"user/{user3}": {"vote_delegated_$1_to_id": user2},
            }
        )
        self.start_poll(1)
        for user_id in (user1, user2):
            self.login(user_id)
            response = self.vote_service.vote({"id": 1, "value": {"1": "Y"}})
            self.assert_status_code(response, 200)
        self.login(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        countdown = self.get_model("projector_countdown/1")
        assert countdown.get("running") is False
        assert countdown.get("countdown_time") == 60
        poll = self.get_model("poll/1")
        assert poll.get("state") == Poll.STATE_FINISHED
        assert poll.get("votescast") == "2.000000"
        assert poll.get("votesinvalid") == "0.000000"
        assert poll.get("votesvalid") == "5.000000"
        assert poll.get("entitled_users_at_stop") == [
            {"voted": True, "user_id": user1, "vote_delegated_to_id": None},
            {"voted": True, "user_id": user2, "vote_delegated_to_id": None},
            {"voted": False, "user_id": user3, "vote_delegated_to_id": user2},
        ]

    def test_stop_entitled_users_at_stop_user_only_once(self) -> None:
        self.set_models(
            {
                "poll/1": {
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                    "entitled_group_ids": [3, 4],
                },
                "user/2": {
                    "is_present_in_meeting_ids": [1],
                },
                "group/3": {"user_ids": [2]},
                "group/4": {"user_ids": [2]},
                "meeting/1": {
                    "group_ids": [3, 4],
                    "is_active_in_organization_id": 1,
                },
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_users_at_stop") == [
            {"voted": False, "user_id": 2, "vote_delegated_to_id": None},
        ]

    def test_stop_entitled_users_not_present(self) -> None:
        self.set_models(
            {
                "poll/1": {
                    "state": Poll.STATE_STARTED,
                    "meeting_id": 1,
                    "entitled_group_ids": [3],
                },
                "user/2": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [3],
                    "meeting_ids": [1],
                },
                "user/3": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [4],
                    "meeting_ids": [1],
                },
                "group/3": {"user_ids": [2], "meeting_id": 1},
                "group/4": {"user_ids": [3], "meeting_id": 1},
                "meeting/1": {
                    "user_ids": [2, 3],
                    "group_ids": [3, 4],
                    "is_active_in_organization_id": 1,
                },
            }
        )
        self.start_poll(1)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_users_at_stop") == [
            {"voted": False, "user_id": 2, "vote_delegated_to_id": None},
        ]

    def test_stop_published(self) -> None:
        self.set_models(
            {
                "poll/1": {"state": Poll.STATE_PUBLISHED, "meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == Poll.STATE_PUBLISHED
        assert (
            "Cannot stop poll 1, because it is not in state started."
            in response.json["message"]
        )

    def test_stop_created(self) -> None:
        self.set_models(
            {
                "poll/1": {"state": Poll.STATE_CREATED, "meeting_id": 1},
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        assert poll.get("state") == Poll.STATE_CREATED
        assert (
            "Cannot stop poll 1, because it is not in state started."
            in response.json["message"]
        )

    def test_stop_no_permissions(self) -> None:
        self.set_models(self.test_models)
        self.start_poll(1)
        self.base_permission_test({}, "poll.stop", {"id": 1})

    def test_stop_permissions(self) -> None:
        self.set_models(self.test_models)
        self.start_poll(1)
        self.base_permission_test(
            {},
            "poll.stop",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )
