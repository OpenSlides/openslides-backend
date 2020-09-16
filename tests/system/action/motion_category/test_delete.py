from tests.system.action.base import BaseActionTestCase


class MotionCategorySystemTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("motion_category/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "motion_category.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_category/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_category/112", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "motion_category.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_category/112")

    def test_delete_handle_remove_relation(self) -> None:
        self.create_model(
            "meeting/222", {"name": "name_xQyvfmsS", "category_ids": [111]}
        )
        self.create_model(
            "motion/89",
            {"name": "name_morZjXig", "meeting_id": 222, "category_id": 89},
        )
        self.create_model(
            "motion_category/111",
            {
                "name": "name_srtgb123",
                "prefix": "prefix_JmDHFgvH",
                "meeting_id": 222,
                "motion_ids": [89],
            },
        )
        model = self.get_model("motion/89")

        assert model.get("category_id") == 89
        self.client.post(
            "/", json=[{"action": "motion_category.delete", "data": [{"id": 111}]}],
        )
        model = self.get_model("motion/89")
        assert model.get("category_id") is None
