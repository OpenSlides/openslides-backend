from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class AssignmentDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(110)

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "assignment/111": {
                    "sequential_number": 1,
                    "meeting_id": 110,
                    "title": "title_srtgb123",
                }
            }
        )
        response = self.request("assignment.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("assignment/111")

    def test_delete_correct_cascading(self) -> None:
        self.set_models(
            {
                "assignment/111": {
                    "sequential_number": 1,
                    "title": "Dr. Assignment",
                    "list_of_speakers_id": 222,
                    "agenda_item_id": 333,
                    "meeting_id": 110,
                    "phase": "finished",
                },
                "list_of_speakers/222": {
                    "sequential_number": 1,
                    "closed": False,
                    "content_object_id": "assignment/111",
                    "meeting_id": 110,
                },
                "agenda_item/333": {
                    "comment": "test_comment_ewoirzewoirioewr",
                    "content_object_id": "assignment/111",
                    "meeting_id": 110,
                },
                "projection/1": {
                    "content_object_id": "assignment/111",
                    "current_projector_id": 1,
                    "meeting_id": 110,
                },
                "projector/1": {
                    "sequential_number": 1,
                    "meeting_id": 110,
                },
                "assignment_candidate/1111": {"assignment_id": 111, "meeting_id": 110},
            }
        )
        response = self.request("assignment.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("assignment/111")
        self.assert_model_not_exists("agenda_item/333")
        self.assert_model_not_exists("list_of_speakers/222")
        self.assert_model_not_exists("projection/1")
        self.assert_model_not_exists("assignment_candidate/1111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "assignment/112": {
                    "sequential_number": 1,
                    "title": "title_srtgb123",
                    "meeting_id": 110,
                }
            }
        )
        response = self.request("assignment.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("assignment/112")
        self.assertEqual(model.get("title"), "title_srtgb123")

    def test_delete_no_permission(self) -> None:
        self.base_permission_test(
            {
                "assignment/111": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "title": "title_srtgb123",
                },
            },
            "assignment.delete",
            {"id": 111},
        )

    def test_delete_permission(self) -> None:
        self.base_permission_test(
            {
                "assignment/111": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "title": "title_srtgb123",
                },
            },
            "assignment.delete",
            {"id": 111},
            Permissions.Assignment.CAN_MANAGE,
        )

    def test_delete_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {
                "assignment/111": {
                    "sequential_number": 1,
                    "meeting_id": 1,
                    "title": "title_srtgb123",
                },
            },
            "assignment.delete",
            {"id": 111},
        )
