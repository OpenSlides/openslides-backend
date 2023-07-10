from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class PointOfOrderCategoryUpdate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: Dict[str, Dict[str, Any]] = {
            "point_of_order_category/37": {
                "text": "blablabla",
                "rank": 11,
                "meeting_id": 1,
            },
        }

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "is_active_in_organization_id": 1,
                    "point_of_order_category_ids": [45],
                },
                "point_of_order_category/45": {
                    "text": "blablabla",
                    "rank": 11,
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "point_of_order_category.update", {"id": 45, "text": "foo", "rank": 12}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "point_of_order_category/45", {"text": "foo", "rank": 12}
        )

    def test_update_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "point_of_order_category.update",
            {"id": 37, "text": "foo", "rank": 12},
        )

    def test_update_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "point_of_order_category.update",
            {"id": 37, "text": "foo", "rank": 12},
            Permissions.Meeting.CAN_MANAGE_SETTINGS,
        )
