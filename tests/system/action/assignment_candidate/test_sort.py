from tests.system.action.base import BaseActionTestCase


class AssignmentCandidateSortActionTest(BaseActionTestCase):
    def test_sort_correct_1(self) -> None:
        self.set_models(
            {
                "assignment/222": {"title": "title_SNLGsvIV"},
                "user/233": {"username": "username_233"},
                "user/234": {"username": "username_234"},
                "assignment_candidate/31": {"assignment_id": 222, "user_id": 233},
                "assignment_candidate/32": {"assignment_id": 222, "user_id": 234},
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
                "assignment/222": {"title": "title_SNLGsvIV"},
                "user/233": {"username": "username_233"},
                "user/234": {"username": "username_234"},
                "assignment_candidate/31": {"assignment_id": 222, "user_id": 233},
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
                "assignment/222": {"title": "title_SNLGsvIV"},
                "user/233": {"username": "username_233"},
                "user/234": {"username": "username_234"},
                "user/236": {"username": "username_236"},
                "assignment_candidate/31": {"assignment_id": 222, "user_id": 233},
                "assignment_candidate/32": {"assignment_id": 222, "user_id": 234},
                "assignment_candidate/33": {"assignment_id": 222, "user_id": 236},
            }
        )
        response = self.request(
            "assignment_candidate.sort",
            {"assignment_id": 222, "candidate_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert "Additional db_instances found." in response.json["message"]
