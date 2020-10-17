from tests.system.action.base import BaseActionTestCase


class MotionCategorySortMotionsInCategoriesActionTest(BaseActionTestCase):
    def test_sort_correct_1(self) -> None:
        self.create_model("motion_category/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion/31", {"category_id": 222, "name": "name_loisueb"})
        self.create_model("motion/32", {"category_id": 222, "name": "name_blanumop"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort_motions_in_categories",
                    "data": [{"id": 222, "motion_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("motion/31")
        assert model_31.get("category_weight") == 2
        model_32 = self.get_model("motion/32")
        assert model_32.get("category_weight") == 1

    def test_sort_missing_model(self) -> None:
        self.create_model("motion_category/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion/31", {"category_id": 222, "name": "name_loisueb"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort_motions_in_categories",
                    "data": [{"id": 222, "motion_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Id 32 not in db_instances." in str(response.data)

    def test_sort_another_section_db(self) -> None:
        self.create_model("motion_category/222", {"name": "name_SNLGsvIV"})
        self.create_model("motion/31", {"category_id": 222, "name": "name_loisueb"})
        self.create_model("motion/32", {"category_id": 222, "name": "name_blanumop"})
        self.create_model("motion/33", {"category_id": 222, "name": "name_polusiem"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.sort_motions_in_categories",
                    "data": [{"id": 222, "motion_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Additional db_instances found." in str(response.data)
