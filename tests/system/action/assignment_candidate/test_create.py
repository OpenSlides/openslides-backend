from tests.system.action.base import BaseActionTestCase


class AssignmentCandidateCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/1333": {"name": "name_JhlFOAfK"},
                "user/110": {"username": "test_Xcdfgee"},
                "assignment/111": {"title": "title_xTcEkItp", "meeting_id": 1333},
            }
        )
        response = self.request(
            "assignment_candidate.create", {"assignment_id": 111, "user_id": 110}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment_candidate/1")
        assert model.get("user_id") == 110
        assert model.get("assignment_id") == 111
        assert model.get("weight") == 10000

    def test_create_empty_data(self) -> None:
        response = self.request("assignment_candidate.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['assignment_id', 'user_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.set_models(
            {
                "user/110": {"username": "test_Xcdfgee"},
                "assignment/111": {"title": "title_xTcEkItp"},
            }
        )
        response = self.request(
            "assignment_candidate.create",
            {
                "wrong_field": "text_AefohteiF8",
                "assignment_id": 111,
                "user_id": 110,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_finished(self) -> None:
        self.set_models(
            {
                "meeting/1333": {"name": "name_JhlFOAfK"},
                "user/110": {"username": "test_Xcdfgee"},
                "assignment/111": {
                    "title": "title_xTcEkItp",
                    "meeting_id": 1333,
                    "phase": "finished",
                },
            }
        )
        response = self.request(
            "assignment_candidate.create", {"assignment_id": 111, "user_id": 110}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "It is not permitted to add a candidate to a finished assignment!",
            response.json["message"],
        )
