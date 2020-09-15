from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionCategorySystemTest(BaseActionTestCase):
    def test_create_good_case_full_fields(self) -> None:
        self.create_model(get_fqid("meeting/222"), {"name": "name_SNLGsvIV"})
        self.create_model(get_fqid("motion_category/123"), {"name": "name_bWdKLQxL"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.create",
                    "data": [
                        {
                            "name": "test_Xcdfgee",
                            "prefix": "prefix_niqCxoXA",
                            "meeting_id": 222,
                            "parent_id": 123,
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_category/124"))
        model = self.datastore.get(get_fqid("motion_category/124"))
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("prefix") == "prefix_niqCxoXA"
        assert model.get("meeting_id") == 222
        assert model.get("parent_id") == 123

    def test_create_good_case_only_required_fields(self) -> None:
        self.create_model(get_fqid("meeting/222"), {"name": "name_SNLGsvIV"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.create",
                    "data": [
                        {
                            "name": "test_Xcdfgee",
                            "prefix": "prefix_niqCxoXA",
                            "meeting_id": 222,
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_category/1"))
        model = self.datastore.get(get_fqid("motion_category/1"))
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("prefix") == "prefix_niqCxoXA"
        assert model.get("meeting_id") == 222

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_category.create", "data": [{}]}],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'prefix\\', \\'meeting_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.create",
                    "data": [
                        {
                            "name": "test_Xcdfgee",
                            "prefix": "prefix_niqCxoXA",
                            "meeting_id": 222,
                            "wrong_field": "text_AefohteiF8",
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain only specified properties", str(response.data),
        )

    def test_create_link_non_existing_meeting(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_category.create",
                    "data": [
                        {
                            "name": "test_Xcdfgee",
                            "prefix": "prefix_niqCxoXA",
                            "meeting_id": 222,
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "You try to reference an instance of meeting that does not exist.",
            str(response.data),
        )
