from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorCountdownUpdate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "projector_countdown/2": {
                    "meeting_id": 1,
                    "title": "test",
                    "default_time": 60,
                    "countdown_time": 60,
                },
            }
        )

    def test_update(self) -> None:
        response = self.request(
            "projector_countdown.update",
            {
                "id": 2,
                "title": "new_title",
                "description": "good bla",
                "default_time": 30,
                "countdown_time": 20,
                "running": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector_countdown/2",
            {
                "title": "new_title",
                "description": "good bla",
                "default_time": 30,
                "countdown_time": 20,
            },
        )

    def test_update_same_title_in_same_id(self) -> None:
        response = self.request(
            "projector_countdown.update", {"id": 2, "title": "test"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector_countdown/2", {"title": "test"})

    def test_update_not_unique_title(self) -> None:
        self.set_models(
            {
                "projector_countdown/3": {
                    "meeting_id": 1,
                    "title": "famousword",
                    "default_time": 60,
                    "countdown_time": 60,
                },
            }
        )
        response = self.request(
            "projector_countdown.update", {"id": 2, "title": "famousword"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Title already exists in this meeting.", response.json["message"]
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_countdown.update",
            {"id": 2, "title": "new_title"},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_countdown.update",
            {"id": 2, "title": "new_title"},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector_countdown.update",
            {"id": 2, "title": "new_title"},
        )
