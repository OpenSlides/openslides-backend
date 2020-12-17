from tests.system.action.base import BaseActionTestCase


class MotionCategorySystemTest(BaseActionTestCase):
    def test_create_good_case_full_fields(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_category/123", {"name": "name_bWdKLQxL", "meeting_id": 222}
        )
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
        self.assert_status_code(response, 200)
        model = self.get_model("motion_category/124")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("prefix") == "prefix_niqCxoXA"
        assert model.get("meeting_id") == 222
        assert model.get("parent_id") == 123
        assert model.get("weight") == 10000
        meeting = self.get_model("meeting/222")
        assert meeting.get("motion_category_ids") == [124]

    def test_create_good_case_only_required_fields(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
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
        self.assert_status_code(response, 200)
        model = self.get_model("motion_category/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("prefix") == "prefix_niqCxoXA"
        assert model.get("meeting_id") == 222

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "motion_category.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain [\\'name\\', \\'prefix\\', \\'meeting_id\\'] properties",
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
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {\\'wrong_field\\'} properties",
            str(response.data),
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
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model \\'meeting/222\\' does not exist",
            str(response.data),
        )
