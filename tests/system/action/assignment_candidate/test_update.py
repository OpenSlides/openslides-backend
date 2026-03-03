from tests.system.action.base import BaseActionTestCase


class AssignmentCandidateSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "assignment/222": {
                    "title": "title_SNLGsvIV",
                    "meeting_id": 1,
                },
                "list_of_speakers/23": {
                    "content_object_id": "assignment/222",
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
                    "weight": 2,
                },
                "assignment_candidate/32": {
                    "assignment_id": 222,
                    "meeting_user_id": 234,
                    "meeting_id": 1,
                    "weight": 1,
                },
            }
        )

    def test_update_correct(self) -> None:
        response = self.request(
            "assignment_candidate.update", {"id": 31, "weight": 3}, internal=True
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("assignment_candidate/31", {"weight": 3})

    def test_update_not_internal(self) -> None:
        response = self.request(
            "assignment_candidate.update", {"id": 31, "weight": 3}, internal=False
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Action assignment_candidate.update does not exist.",
            response.json["message"],
        )
