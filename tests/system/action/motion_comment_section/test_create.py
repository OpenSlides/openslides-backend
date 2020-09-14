from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionCommentSectionActionTest(BaseActionTestCase):
    def test_create_good_case_required_fields(self) -> None:
        self.create_model(get_fqid("meeting/222"), {"name": "name_SNLGsvIV"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_comment_section.create",
                    "data": [{"name": "test_Xcdfgee", "meeting_id": 222}],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_comment_section/1"))
        model = self.datastore.get(get_fqid("motion_comment_section/1"))
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("weight") == 0

    def test_create_good_case_all_fields(self) -> None:
        self.create_model(get_fqid("meeting/222"), {"name": "name_SNLGsvIV"})
        self.create_model(get_fqid("group/23"), {"name": "name_IIwngcUT"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_comment_section.create",
                    "data": [
                        {
                            "name": "test_Xcdfgee",
                            "meeting_id": 222,
                            "read_group_ids": [23],
                            "write_group_ids": [23],
                        }
                    ],
                }
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("motion_comment_section/1"))
        model = self.datastore.get(get_fqid("motion_comment_section/1"))
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("weight") == 0
        assert model.get("read_group_ids") == [23]
        assert model.get("write_group_ids") == [23]

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_comment_section.create", "data": [{}]}],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'meeting_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        self.create_model(get_fqid("meeting/222"), {"name": "name_SNLGsvIV"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_comment_section.create",
                    "data": [
                        {
                            "name": "name_test1",
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
