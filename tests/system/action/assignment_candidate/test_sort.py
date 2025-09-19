from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AssignmentCandidateSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "assignment/222": {
                "sequential_number": 1,
                "title": "title_SNLGsvIV",
                "meeting_id": 1,
            },
            "user/233": {"username": "username_233"},
            "user/234": {"username": "username_234"},
            "meeting_user/233": {"meeting_id": 1, "user_id": 233},
            "meeting_user/234": {"meeting_id": 1, "user_id": 234},
            "assignment_candidate/31": {
                "assignment_id": 222,
                "meeting_user_id": 233,
                "meeting_id": 1,
            },
            "assignment_candidate/32": {
                "assignment_id": 222,
                "meeting_user_id": 234,
                "meeting_id": 1,
            },
        }

    def test_sort_correct_1(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "assignment/222": {
                    "sequential_number": 1,
                    "title": "title_SNLGsvIV",
                    "meeting_id": 1,
                },
                "user/233": {"username": "username_233"},
                "user/234": {"username": "username_234"},
                "meeting_user/233": {"meeting_id": 1, "user_id": 233},
                "meeting_user/234": {"meeting_id": 1, "user_id": 234},
                "assignment_candidate/31": {
                    "assignment_id": 222,
                    "meeting_user_id": 233,
                    "meeting_id": 1,
                },
                "assignment_candidate/32": {
                    "assignment_id": 222,
                    "meeting_user_id": 234,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("assignment_candidate/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("assignment_candidate/32")
        assert model_32.get("weight") == 1

    def test_sort_missing_model(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "assignment/222": {
                    "sequential_number": 1,
                    "title": "title_SNLGsvIV",
                    "meeting_id": 1,
                },
                "user/233": {"username": "username_233"},
                "user/234": {"username": "username_234"},
                "meeting_user/233": {"meeting_id": 1, "user_id": 233},
                "meeting_user/234": {"meeting_id": 1, "user_id": 234},
                "assignment_candidate/31": {
                    "assignment_id": 222,
                    "meeting_user_id": 233,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "assignment_candidate sorting failed, because element assignment_candidate/32 doesn't exist."
            in response.json["message"]
        )

    def test_sort_another_section_db(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "assignment/222": {
                    "sequential_number": 1,
                    "title": "title_SNLGsvIV",
                    "meeting_id": 1,
                },
                "user/233": {"username": "username_233"},
                "user/234": {"username": "username_234"},
                "user/236": {"username": "username_236"},
                "meeting_user/233": {"meeting_id": 1, "user_id": 233},
                "meeting_user/234": {"meeting_id": 1, "user_id": 234},
                "meeting_user/236": {"meeting_id": 1, "user_id": 236},
                "assignment_candidate/31": {
                    "assignment_id": 222,
                    "meeting_user_id": 233,
                    "meeting_id": 1,
                },
                "assignment_candidate/32": {
                    "assignment_id": 222,
                    "meeting_user_id": 234,
                    "meeting_id": 1,
                },
                "assignment_candidate/33": {
                    "assignment_id": 222,
                    "meeting_user_id": 236,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "assignment_candidate sorting failed, because some elements were not included in the call."
            in response.json["message"]
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
            Permissions.Assignment.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
        )
