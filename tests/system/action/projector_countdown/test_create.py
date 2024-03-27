from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorCountdown(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {
                    "projector_countdown_default_time": 11,
                    "is_active_in_organization_id": 1,
                },
                "projector_countdown/1": {"title": "blablabla", "meeting_id": 1},
            }
        )

    def test_create(self) -> None:
        response = self.request(
            "projector_countdown.create",
            {
                "meeting_id": 1,
                "title": "test",
                "description": "good description",
                "default_time": 30,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("projector_countdown/2")
        assert model.get("title") == "test"
        assert model.get("meeting_id") == 1
        assert model.get("description") == "good description"
        assert model.get("default_time") == 30
        assert model.get("countdown_time") == 30

    def test_create_title_not_unique(self) -> None:
        response = self.request(
            "projector_countdown.create",
            {
                "meeting_id": 1,
                "title": "blablabla",
                "description": "good description",
                "default_time": 30,
            },
        )
        self.assert_status_code(response, 400)
        assert "Title already exists in this meeting." in response.data.decode()

    def test_create_no_default_time(self) -> None:
        response = self.request(
            "projector_countdown.create",
            {
                "meeting_id": 1,
                "title": "test2",
                "description": "good description",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("projector_countdown/2")
        assert model.get("title") == "test2"
        assert model.get("default_time") == 11
        assert model.get("countdown_time") == 11

    def test_create_zero_default_time(self) -> None:
        response = self.request(
            "projector_countdown.create",
            {
                "meeting_id": 1,
                "title": "test2",
                "description": "good description",
                "default_time": 0,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("projector_countdown/2")
        assert model.get("title") == "test2"
        assert model.get("default_time") == 0
        assert model.get("countdown_time") == 0

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_countdown.create",
            {
                "meeting_id": 1,
                "title": "test",
                "description": "good description",
                "default_time": 30,
            },
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector_countdown.create",
            {
                "meeting_id": 1,
                "title": "test",
                "description": "good description",
                "default_time": 30,
            },
            Permissions.Projector.CAN_MANAGE,
        )
