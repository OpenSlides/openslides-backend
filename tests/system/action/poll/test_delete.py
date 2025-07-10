from unittest.mock import Mock, patch

from openslides_backend.permissions.permissions import Permissions
from tests.system.util import CountDatastoreCalls, Profiler, performance

from .base_poll_test import BasePollTestCase
from .poll_test_mixin import PollTestMixin


class PollDeleteTest(PollTestMixin, BasePollTestCase):
    @patch("openslides_backend.services.vote.adapter.VoteAdapter.clear")
    def test_delete_correct(self, clear: Mock) -> None:
        """
        Also ensures that the vote service is notified on success if the poll is started.
        """
        clear_called_on: list[int] = []

        def add_to_list(id_: int) -> None:
            clear_called_on.append(id_)

        clear.side_effect = add_to_list
        self.create_meeting()
        self.set_models(
            {
                "poll/111": {
                    "meeting_id": 1,
                    "content_object_id": "motion/1",
                    "state": "started",
                },
                "motion/1": {"meeting_id": 1, "poll_ids": [111]},
            }
        )
        response = self.request("poll.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("poll/111")
        self.assert_history_information("motion/1", ["Voting deleted"])
        assert clear_called_on == [111]

    def test_delete_wrong_id(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "poll/112": {"meeting_id": 1},
            }
        )
        response = self.request("poll.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("poll/112")

    @patch("openslides_backend.services.vote.adapter.VoteAdapter.clear")
    def test_delete_correct_cascading(self, clear: Mock) -> None:
        """
        Also ensures that the vote service is not notified if the poll wasn't started anyway.
        """
        clear_called_on: list[int] = []

        def add_to_list(id_: int) -> None:
            clear_called_on.append(id_)

        clear.side_effect = add_to_list
        self.create_meeting()
        self.set_models(
            {
                "topic/1": {"poll_ids": [111], "meeting_id": 1},
                "poll/111": {
                    "option_ids": [42],
                    "meeting_id": 1,
                    "projection_ids": [1],
                    "content_object_id": "topic/1",
                },
                "option/42": {"poll_id": 111, "meeting_id": 1},
                "meeting/1": {
                    "all_projection_ids": [1],
                    "topic_ids": [1],
                },
                "projection/1": {
                    "content_object_id": "poll/111",
                    "current_projector_id": 1,
                    "meeting_id": 1,
                },
                "projector/1": {
                    "current_projection_ids": [1],
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("poll.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("poll/111")
        self.assert_model_deleted("option/42")
        self.assert_model_deleted("projection/1")
        self.assert_model_exists("projector/1", {"current_projection_ids": []})
        assert clear_called_on == []

    def test_delete_cascading_poll_candidate_list(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "topic/1": {"poll_ids": [111], "meeting_id": 1},
                "poll/111": {
                    "option_ids": [42],
                    "meeting_id": 1,
                    "content_object_id": "topic/1",
                },
                "option/42": {
                    "poll_id": 111,
                    "meeting_id": 1,
                    "content_object_id": "poll_candidate_list/12",
                },
                "meeting/1": {
                    "poll_candidate_list_ids": [12],
                    "poll_candidate_ids": [13],
                    "topic_ids": [1],
                },
                "poll_candidate_list/12": {
                    "meeting_id": 1,
                    "option_id": 42,
                    "poll_candidate_ids": [13],
                },
                "poll_candidate/13": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "weight": 1,
                    "poll_candidate_list_id": 12,
                },
                "user/1": {"poll_candidate_ids": [13]},
            }
        )
        response = self.request("poll.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("poll/111")
        self.assert_model_deleted("option/42")
        self.assert_model_deleted("poll_candidate_list/12")

    @patch("openslides_backend.services.vote.adapter.VoteAdapter.clear")
    def test_delete_no_permissions(self, clear: Mock) -> None:
        """
        Also ensures that the vote service is not notified if the action failed.
        """
        clear_called_on: list[int] = []

        def add_to_list(id_: int) -> None:
            clear_called_on.append(id_)

        clear.side_effect = add_to_list
        self.base_permission_test(
            {
                "poll/111": {
                    "meeting_id": 1,
                    "content_object_id": "topic/1",
                    "state": "started",
                }
            },
            "poll.delete",
            {"id": 111},
        )

        assert clear_called_on == []

    def test_delete_permissions(self) -> None:
        self.set_models(
            {
                "topic/1": {"title": "The topic", "meeting_id": 1},
                "meeting/1": {"topic_ids": [1]},
            }
        )
        self.base_permission_test(
            {"poll/111": {"meeting_id": 1, "content_object_id": "topic/1"}},
            "poll.delete",
            {"id": 111},
            Permissions.Poll.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {"poll/111": {"meeting_id": 1, "content_object_id": "topic/1"}},
            "poll.delete",
            {"id": 111},
        )

    def test_delete_datastore_calls(self) -> None:
        self.prepare_users_and_poll(3)

        with CountDatastoreCalls() as counter:
            response = self.request("poll.delete", {"id": 1})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("poll/1")
        assert counter.calls == 7

    @performance
    def test_delete_performance(self) -> None:
        user_ids = self.prepare_users_and_poll(1000)
        response = self.request("poll.stop", {"id": 1})
        self.assert_status_code(response, 200)
        self.datastore.reset(hard=True)

        with Profiler("test_delete_performance.prof"):
            response = self.request("poll.delete", {"id": 1})

        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll["voted_ids"] == user_ids
