from tests.system.action.base import BaseActionTestCase


class GroupCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/22", {"name": "name_vJxebUwo"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "group.create",
                    "data": [{"name": "test_Xcdfgee", "meeting_id": 22}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 22
        assert model.get("permissions") == []

    def test_create_permissions(self) -> None:
        self.create_model("meeting/22", {"name": "name_vJxebUwo"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "group.create",
                    "data": [
                        {
                            "name": "test_Xcdfgee",
                            "meeting_id": 22,
                            "permissions": ["agenda_item.can_see"],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("group/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("meeting_id") == 22
        assert model.get("permissions") == ["agenda_item.can_see"]

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "group.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name', 'meeting_id'] properties",
            response.json.get("message", ""),
        )

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/22", {"name": "name_vJxebUwo"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "group.create",
                    "data": [
                        {
                            "wrong_field": "text_AefohteiF8",
                            "name": "test1",
                            "meeting_id": 22,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json.get("message", ""),
        )
