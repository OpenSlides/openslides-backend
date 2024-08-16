from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorCountdownUpdate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "projector_countdown/2": {
                    "meeting_id": 1,
                    "title": "test",
                    "description": "blablabla",
                    "default_time": 60,
                    "countdown_time": 60,
                },
                "projector_countdown/3": {
                    "meeting_id": 1,
                    "title": "famousword",
                    "description": "blablabla",
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
        model = self.get_model("projector_countdown/2")
        assert model.get("title") == "new_title"
        assert model.get("description") == "good bla"
        assert model.get("default_time") == 30
        assert model.get("countdown_time") == 20

    def test_update_same_title_in_same_id(self) -> None:
        response = self.request(
            "projector_countdown.update",
            {
                "id": 2,
                "title": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("projector_countdown/2")
        assert model.get("title") == "test"

    def test_update_not_unique_title(self) -> None:
        response = self.request(
            "projector_countdown.update", {"id": 2, "title": "famousword"}
        )
        self.assert_status_code(response, 400)
        assert "Title already exists in this meeting." in response.data.decode()

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
