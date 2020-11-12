from tests.system.action.base import BaseActionTestCase


class MeetingSetFontActionTest(BaseActionTestCase):
    def test_set_font_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_meeting222"})
        self.create_model(
            "mediafile/17",
            {"is_directory": False, "mimetype": "font/woff", "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.set_font",
                    "data": [{"id": 222, "mediafile_id": 17, "place": "1"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("font_$1_id") == 17

    def test_set_font_wrong_directory(self) -> None:
        self.create_model("meeting/222", {"name": "name_meeting222"})
        self.create_model(
            "mediafile/17",
            {"is_directory": True, "mimetype": "font/ttf", "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.set_font",
                    "data": [{"id": 222, "mediafile_id": 17, "place": "1"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Cannot set a directory." in str(response.data)

    def test_set_font_wrong_no_image(self) -> None:
        self.create_model("meeting/222", {"name": "name_meeting222"})
        self.create_model(
            "mediafile/17",
            {"is_directory": False, "mimetype": "text/plain", "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.set_font",
                    "data": [{"id": 222, "mediafile_id": 17, "place": "1"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Invalid mimetype" in str(response.data)
