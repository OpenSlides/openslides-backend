from tests.system.action.base import BaseActionTestCase


class TagActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_meeting(577)
        response = self.request(
            "tag.create", {"name": "test_Xcdfgee", "meeting_id": 577}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("tag/1")
        self.assertEqual(model.get("name"), "test_Xcdfgee")
        self.assertEqual(model.get("meeting_id"), 577)

    def test_create_empty_data(self) -> None:
        response = self.request("tag.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'name'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_meeting(577)
        response = self.request(
            "tag.create",
            {
                "name": "test_Xcdfgee",
                "meeting_id": 577,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.set_organization_management_level(None)
        self.create_meeting(577)
        response = self.request(
            "tag.create", {"name": "test_Xcdfgee", "meeting_id": 577}
        )
        self.assert_status_code(response, 403)
        self.assert_model_not_exists("tag/1")
        self.assertIn(
            "You are not allowed to perform action tag.create. Missing Permission: tag.can_manage",
            response.json["message"],
        )
