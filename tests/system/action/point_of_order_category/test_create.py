from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class PointOfOrderCategoryCreate(BaseActionTestCase):
    def test_create_correct(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_meeting_110",
                    "is_active_in_organization_id": 1,
                },
            }
        )
        response = self.request(
            "point_of_order_category.create",
            {"text": "blablabla", "rank": 11, "meeting_id": 110},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "point_of_order_category/1",
            {"text": "blablabla", "rank": 11, "meeting_id": 110},
        )
        self.assert_model_exists("meeting/110", {"point_of_order_category_ids": [1]})

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "point_of_order_category.create",
            {"text": "blablabla", "rank": 11, "meeting_id": 1},
        )

    def test_create_permission(self) -> None:
        self.base_permission_test(
            {},
            "point_of_order_category.create",
            {"text": "blablabla", "rank": 11, "meeting_id": 1},
            Permissions.Meeting.CAN_MANAGE_SETTINGS,
        )

    def test_create_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "point_of_order_category.create",
            {"text": "blablabla", "rank": 11, "meeting_id": 1},
        )
