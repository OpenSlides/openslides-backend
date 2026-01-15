from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions

from .base_poll_test import BasePollTestCase


class PollAnonymize(BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "poll/1": {
                    "option_ids": [1],
                    "global_option_id": 2,
                    "meeting_id": 1,
                    "state": Poll.STATE_FINISHED,
                    "type": Poll.TYPE_NAMED,
                    "content_object_id": "topic/1",
                },
                "topic/1": {"meeting_id": 1},
                "option/1": {"vote_ids": [1], "meeting_id": 1},
                "option/2": {"vote_ids": [2], "meeting_id": 1},
                "vote/1": {
                    "user_id": 1,
                    "meeting_id": 1,
                    "delegated_user_id": 1,
                },
                "vote/2": {
                    "user_id": 1,
                    "meeting_id": 1,
                    "delegated_user_id": 1,
                },
                "user/1": {
                    "meeting_user_ids": [11],
                    "delegated_vote_ids": [1, 2],
                    "vote_ids": [1, 2],
                },
                "meeting_user/11": {
                    "meeting_id": 1,
                    "user_id": 1,
                },
            }
        )

    def assert_anonymize(self) -> None:
        poll = self.get_model("poll/1")
        assert poll.get("is_pseudoanonymized") is True
        for fqid in ("vote/1", "vote/2"):
            vote = self.get_model(fqid)
            assert vote.get("user_id") is None
            assert vote.get("delegated_user_id") is None
        self.assert_model_exists("user/1", {"vote_ids": [], "delegated_vote_ids": []})

    def test_anonymize(self) -> None:
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_anonymize()
        self.assert_history_information("topic/1", None)

    def test_anonymize_motion_poll(self) -> None:
        self.set_models(
            {
                "motion/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "content_object_id": "motion/1",
                },
            }
        )
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/1", ["Voting anonymized"])

    def test_anonymize_assignment_poll(self) -> None:
        self.set_models(
            {
                "assignment/1": {
                    "meeting_id": 1,
                },
                "poll/1": {
                    "content_object_id": "assignment/1",
                },
            }
        )
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", ["Ballot anonymized"])

    def test_anonymize_publish_state(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_PUBLISHED})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_anonymize()

    def test_anonymize_wrong_state(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_CREATED})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id") == 1
            assert vote.get("delegated_user_id") == 1

    def test_anonymize_wrong_type(self) -> None:
        self.update_model("poll/1", {"type": Poll.TYPE_ANALOG})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id") == 1
            assert vote.get("delegated_user_id") == 1

    def test_anonymize_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "poll.anonymize",
            {"id": 1},
        )

    def test_anonymize_permissions(self) -> None:
        self.base_permission_test(
            {},
            "poll.anonymize",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_anonymize_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "poll.anonymize",
            {"id": 1},
        )
