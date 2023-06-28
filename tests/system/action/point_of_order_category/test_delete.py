from tests.system.action.base import BaseActionTestCase


class PointOfOrderCategoryDelete(BaseActionTestCase):
    def test_delete_correct(self) -> None:
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
        response = self.request("point_of_order_category.delete", {"id": 45})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("point_of_order_category/45")
        self.assert_model_exists("meeting/110", {"point_of_order_category_ids": []})
