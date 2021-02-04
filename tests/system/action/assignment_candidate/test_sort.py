from tests.system.action.base import BaseActionTestCase


class AssignmentCandidateSortActionTest(BaseActionTestCase):
    def test_sort_correct_1(self) -> None:
        self.create_model("assignment/222", {"title": "title_SNLGsvIV"})
        self.create_model("user/233", {"username": "username_233"})
        self.create_model("user/234", {"username": "username_234"})
        self.create_model(
            "assignment_candidate/31", {"assignment_id": 222, "user_id": 233}
        )
        self.create_model(
            "assignment_candidate/32", {"assignment_id": 222, "user_id": 234}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment_candidate.sort",
                    "data": [{"assignment_id": 222, "candidate_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("assignment_candidate/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("assignment_candidate/32")
        assert model_32.get("weight") == 1

    def test_sort_missing_model(self) -> None:
        self.create_model("assignment/222", {"title": "title_SNLGsvIV"})
        self.create_model("user/233", {"username": "username_233"})
        self.create_model("user/234", {"username": "username_234"})
        self.create_model(
            "assignment_candidate/31", {"assignment_id": 222, "user_id": 233}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment_candidate.sort",
                    "data": [{"assignment_id": 222, "candidate_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Id 32 not in db_instances." in response.json.get("message", "")

    def test_sort_another_section_db(self) -> None:
        self.create_model("assignment/222", {"title": "title_SNLGsvIV"})
        self.create_model("user/233", {"username": "username_233"})
        self.create_model("user/234", {"username": "username_234"})
        self.create_model("user/236", {"username": "username_236"})
        self.create_model(
            "assignment_candidate/31", {"assignment_id": 222, "user_id": 233}
        )
        self.create_model(
            "assignment_candidate/32", {"assignment_id": 222, "user_id": 234}
        )
        self.create_model(
            "assignment_candidate/33", {"assignment_id": 222, "user_id": 236}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment_candidate.sort",
                    "data": [{"assignment_id": 222, "candidate_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Additional db_instances found." in response.json.get("message", "")
