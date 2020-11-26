from tests.system.action.base import BaseActionTestCase


class AssignmentCandidateCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/1333", {"name": "name_JhlFOAfK"})
        self.create_model("user/110", {"username": "test_Xcdfgee"})
        self.create_model(
            "assignment/111", {"title": "title_xTcEkItp", "meeting_id": 1333}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment_candidate.create",
                    "data": [{"assignment_id": 111, "user_id": 110}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment_candidate/1")
        assert model.get("user_id") == 110
        assert model.get("assignment_id") == 111
        assert model.get("weight") == 10000

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "assignment_candidate.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain [\\'assignment_id\\', \\'user_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        self.create_model("user/110", {"username": "test_Xcdfgee"})
        self.create_model("assignment/111", {"title": "title_xTcEkItp"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment_candidate.create",
                    "data": [
                        {
                            "wrong_field": "text_AefohteiF8",
                            "assignment_id": 111,
                            "user_id": 110,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )
