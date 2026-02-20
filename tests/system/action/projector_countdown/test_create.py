from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorCountdown(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models({"meeting/1": {"projector_countdown_default_time": 11}})

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
        self.assert_model_exists(
            "projector_countdown/1",
            {
                "title": "test",
                "meeting_id": 1,
                "description": "good description",
                "default_time": 30,
                "countdown_time": 30,
            },
        )

    def test_create_title_not_unique(self) -> None:
        self.set_models(
            {"projector_countdown/1": {"title": "blablabla", "meeting_id": 1}}
        )
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
        self.assertEqual(
            "Title already exists in this meeting.", response.json["message"]
        )

    def test_create_no_default_time(self) -> None:
        response = self.request(
            "projector_countdown.create",
            {"meeting_id": 1, "title": "test2", "description": "good description"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector_countdown/1",
            {"title": "test2", "default_time": 11, "countdown_time": 11},
        )

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
        self.assert_model_exists(
            "projector_countdown/1",
            {"title": "test2", "default_time": 0, "countdown_time": 0},
        )

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

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector_countdown.create",
            {
                "meeting_id": 1,
                "title": "test",
                "description": "good description",
                "default_time": 30,
            },
        )
