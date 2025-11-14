from typing import Any

from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.services.database.interface import PartialModel

from .base_poll_test import BasePollTestCase


class PollAnonymize(BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_topic(1, 1)
        self.set_user_groups(1, [1])
        self.test_data: dict[str, dict[str, Any]] = {
            "poll/1": {
                "title": "Poll 1",
                "global_option_id": 2,
                "meeting_id": 1,
                "state": Poll.STATE_FINISHED,
                "type": Poll.TYPE_NAMED,
                "content_object_id": "topic/1",
                "pollmethod": "Y",
                "onehundred_percent_base": Poll.ONEHUNDRED_PERCENT_BASE_Y,
            },
            "option/1": {"meeting_id": 1, "poll_id": 1},
            "option/2": {"meeting_id": 1, "poll_id": 1},
            "vote/1": {
                "user_id": 1,
                "meeting_id": 1,
                "delegated_user_id": 1,
                "user_token": "abc",
                "option_id": 1,
            },
            "vote/2": {
                "user_id": 1,
                "meeting_id": 1,
                "delegated_user_id": 1,
                "user_token": "edf",
                "option_id": 2,
            },
        }

    def set_test_data(self, poll_data: PartialModel = {}) -> None:
        if poll_data:
            self.test_data["poll/1"].update(poll_data)
        self.set_models(self.test_data)

    def assert_anonymize(self) -> None:
        self.assert_model_exists("poll/1", {"is_pseudoanonymized": True})
        for fqid in ("vote/1", "vote/2"):
            self.assert_model_exists(fqid, {"user_id": None, "delegated_user_id": None})
        self.assert_model_exists(
            "user/1", {"vote_ids": None, "delegated_vote_ids": None}
        )

    def test_anonymize(self) -> None:
        self.set_test_data()
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_anonymize()
        self.assert_history_information("topic/1", ["Voting anonymized"])

    def test_anonymize_assignment_poll(self) -> None:
        self.create_assignment(1, 1)
        self.set_test_data({"content_object_id": "assignment/1"})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_history_information("assignment/1", ["Ballot anonymized"])

    def test_anonymize_publish_state(self) -> None:
        self.set_test_data({"state": Poll.STATE_PUBLISHED})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_anonymize()

    def test_anonymize_wrong_state(self) -> None:
        self.set_test_data({"state": Poll.STATE_CREATED})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            self.assert_model_exists(vote_fqid, {"user_id": 1, "delegated_user_id": 1})
        self.assertEqual(
            "Anonymizing can only be done after finishing a poll.",
            response.json["message"],
        )

    def test_anonymize_wrong_type(self) -> None:
        self.set_test_data({"type": Poll.TYPE_ANALOG})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            self.assert_model_exists(vote_fqid, {"user_id": 1, "delegated_user_id": 1})
        self.assertEqual(
            "You can only anonymize named polls.",
            response.json["message"],
        )

    def test_anonymize_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_data,
            "poll.anonymize",
            {"id": 1},
        )

    def test_anonymize_permissions(self) -> None:
        self.base_permission_test(
            self.test_data,
            "poll.anonymize",
            {"id": 1},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_anonymize_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.test_data,
            "poll.anonymize",
            {"id": 1},
        )
