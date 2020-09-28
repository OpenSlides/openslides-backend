from tests.system.action.base import BaseActionTestCase


class AssignmentCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_zvfbAjpZ", "agenda_item_creation": "always"}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment.create",
                    "data": [{"title": "test_Xcdfgee", "meeting_id": 110}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 110)
        self.assertEqual(agenda_item.get("content_object_id"), "assignment/1")

    def test_create_other_agenda_item_check(self) -> None:
        self.create_model(
            "meeting/110",
            {"name": "name_zvfbAjpZ", "agenda_item_creation": "default_yes"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment.create",
                    "data": [{"title": "test_Xcdfgee", "meeting_id": 110}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 110)
        self.assertEqual(agenda_item.get("content_object_id"), "assignment/1")

    def test_create_other_agenda_item_check_2(self) -> None:
        self.create_model(
            "meeting/110",
            {"name": "name_zvfbAjpZ", "agenda_item_creation": "default_no"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment.create",
                    "data": [{"title": "test_Xcdfgee", "meeting_id": 110}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        self.assert_model_not_exists("agenda_item/1")

    def test_create_other_agenda_item_check_3(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_zvfbAjpZ", "agenda_item_creation": "never"}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 110,
                            "agenda_create": True,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        self.assert_model_not_exists("agenda_item/1")

    def test_create_full_fields(self) -> None:
        self.create_model(
            "meeting/110",
            {"name": "name_zvfbAjpZ", "agenda_item_creation": "default_yes"},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 110,
                            "description": "text_test1",
                            "open_posts": 12,
                            "phase": 1,
                            "default_poll_description": "text_test2",
                            "number_poll_candidates": True,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        assert model.get("description") == "text_test1"
        assert model.get("open_posts") == 12
        assert model.get("phase") == 1
        assert model.get("default_poll_description") == "text_test2"
        assert model.get("number_poll_candidates") is True
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 110)
        self.assertEqual(agenda_item.get("content_object_id"), "assignment/1")

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "assignment.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'title\\', \\'meeting_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/110", {"name": "name_zvfbAjpZ"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "assignment.create",
                    "data": [
                        {
                            "title": "title_Xcdfgee",
                            "meeting_id": 110,
                            "wrong_field": "text_AefohteiF8",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )
