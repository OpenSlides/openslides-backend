from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MeetingDeleteAllSpeakersOfAllListsActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/1": {
                "title": "motion1",
                "sequential_number": 1,
                "state_id": 1,
                "meeting_id": 1,
            },
            "list_of_speakers/11": {
                "meeting_id": 1,
                "sequential_number": 11,
                "content_object_id": "motion/1",
            },
            "speaker/1": {"list_of_speakers_id": 11, "meeting_id": 1},
        }

    def test_no_los(self) -> None:
        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 1})
        self.assert_status_code(response, 200)

    def test_one_los_empty(self) -> None:
        self.create_motion(1)
        self.set_models(
            {
                "list_of_speakers/11": {
                    "meeting_id": 1,
                    "sequential_number": 1,
                    "content_object_id": "motion/1",
                },
            }
        )
        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 1})
        self.assert_status_code(response, 200)

    def test_1_los_1_speaker(self) -> None:
        self.set_models(self.permission_test_models)
        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/1")

    def test_1_los_2_speakers(self) -> None:
        self.set_models(self.permission_test_models)
        self.set_models({"speaker/2": {"list_of_speakers_id": 11, "meeting_id": 1}})
        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/1")
        self.assert_model_not_exists("speaker/2")

    def test_3_los(self) -> None:
        self.create_motion(1, 1)
        self.create_motion(1, 2)
        self.create_motion(1, 3)
        self.set_models(
            {
                "list_of_speakers/11": {
                    "meeting_id": 1,
                    "sequential_number": 11,
                    "content_object_id": "motion/1",
                },
                "speaker/1": {"list_of_speakers_id": 11, "meeting_id": 1},
                "speaker/2": {"list_of_speakers_id": 11, "meeting_id": 1},
                "list_of_speakers/12": {
                    "meeting_id": 1,
                    "sequential_number": 12,
                    "content_object_id": "motion/2",
                },
                "list_of_speakers/13": {
                    "meeting_id": 1,
                    "sequential_number": 13,
                    "content_object_id": "motion/3",
                },
                "speaker/3": {"list_of_speakers_id": 13, "meeting_id": 1},
            }
        )

        response = self.request("meeting.delete_all_speakers_of_all_lists", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("speaker/1")
        self.assert_model_not_exists("speaker/2")
        self.assert_model_not_exists("speaker/3")

    def test_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.delete_all_speakers_of_all_lists",
            {"id": 1},
        )

    def test_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.delete_all_speakers_of_all_lists",
            {"id": 1},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )

    def test_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "meeting.delete_all_speakers_of_all_lists",
            {"id": 1},
        )
