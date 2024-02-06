from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectionUpdateOptions(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"name": "bla", "is_active_in_organization_id": 1},
            "projector/23": {"meeting_id": 1, "current_projection_ids": [33]},
            "projection/33": {"meeting_id": 1, "current_projector_id": 23},
        }

    def test_correct(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "projection.update_options",
            {
                "id": 33,
                "options": {"bla": []},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projection/33", {"options": {"bla": []}})

    def test_no_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "projection.update_options",
            {
                "id": 33,
                "options": {"bla": []},
            },
        )

    def test_permissions(self) -> None:
        self.base_permission_test(
            self.test_models,
            "projection.update_options",
            {
                "id": 33,
                "options": {"bla": []},
            },
            Permissions.Projector.CAN_MANAGE,
        )
