from openslides_backend.shared.exceptions import DatabaseException
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionCategorySystemTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model(get_fqid("motion_category/111"), {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "motion_category.delete", "data": [{"id": 111}]}],
        )
        self.assertEqual(response.status_code, 200)
        model = self.datastore.get(
            get_fqid("motion_category/111"), get_deleted_models=2
        )
        assert model.get("meta_deleted")

    def test_delete_wrong_id(self) -> None:
        self.create_model(get_fqid("motion_category/112"), {"name": "name_srtgb123"})
        with self.assertRaises(DatabaseException):
            self.client.post(
                "/", json=[{"action": "motion_category.delete", "data": [{"id": 111}]}],
            )
        self.assert_model_exists(get_fqid("motion_category/112"))

    def test_delete_handle_remove_releation(self) -> None:
        self.create_model(
            get_fqid("meeting/222"), {"name": "name_xQyvfmsS", "category_ids": [111]}
        )
        self.create_model(
            get_fqid("motion/89"),
            {"name": "name_morZjXig", "meeting_id": 222, "category_id": 89},
        )
        self.create_model(
            get_fqid("motion_category/111"),
            {
                "name": "name_srtgb123",
                "prefix": "prefix_JmDHFgvH",
                "meeting_id": 222,
                "motion_ids": [89],
            },
        )
        model = self.datastore.get(get_fqid("motion/89"))

        assert model.get("category_id") == 89
        self.client.post(
            "/", json=[{"action": "motion_category.delete", "data": [{"id": 111}]}],
        )
        model = self.datastore.get(get_fqid("motion/89"))
        assert model.get("category_id") is None
