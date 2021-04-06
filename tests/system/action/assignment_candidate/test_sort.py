from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AssignmentCandidateSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "assignment/222": {"title": "title_SNLGsvIV", "meeting_id": 1},
            "user/233": {"username": "username_233"},
            "user/234": {"username": "username_234"},
            "assignment_candidate/31": {
                "assignment_id": 222,
                "user_id": 233,
                "meeting_id": 1,
            },
            "assignment_candidate/32": {
                "assignment_id": 222,
                "user_id": 234,
                "meeting_id": 1,
            },
        }

    def test_sort_correct_1(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "assignment/222": {"title": "title_SNLGsvIV", "meeting_id": 1},
                "user/233": {"username": "username_233"},
                "user/234": {"username": "username_234"},
                "assignment_candidate/31": {
                    "assignment_id": 222,
                    "user_id": 233,
                    "meeting_id": 1,
                },
                "assignment_candidate/32": {
                    "assignment_id": 222,
                    "user_id": 234,
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
        self.set_models(
            {
                "meeting/1": {},
                "assignment/222": {"title": "title_SNLGsvIV", "meeting_id": 1},
                "user/233": {"username": "username_233"},
                "user/234": {"username": "username_234"},
                "assignment_candidate/31": {
                    "assignment_id": 222,
                    "user_id": 233,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert "Id 32 not in db_instances." in response.json["message"]

    def test_sort_another_section_db(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "assignment/222": {"title": "title_SNLGsvIV", "meeting_id": 1},
                "user/233": {"username": "username_233"},
                "user/234": {"username": "username_234"},
                "user/236": {"username": "username_236"},
                "assignment_candidate/31": {
                    "assignment_id": 222,
                    "user_id": 233,
                    "meeting_id": 1,
                },
                "assignment_candidate/32": {
                    "assignment_id": 222,
                    "user_id": 234,
                    "meeting_id": 1,
                },
                "assignment_candidate/33": {
                    "assignment_id": 222,
                    "user_id": 236,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert "Additional db_instances found." in response.json["message"]

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
            Permissions.Assignment.CAN_MANAGE,
        )
