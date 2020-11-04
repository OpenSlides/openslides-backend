from tests.system.action.base import BaseActionTestCase


class MediafileUnsetFontActionTest(BaseActionTestCase):
    def test_unset_font(self) -> None:
        self.create_model(
            "meeting/222",
            {"name": "name_meeting222", "font_$1_id": 17, "font_$2_id": 17},
        )
        self.create_model(
            "mediafile/17",
            {"is_directory": False, "mimetype": "image/png", "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.unset_font",
                    "data": [{"id": 222, "place": "2"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("font_$2_id") is None
        assert model.get("font_$1_id") == 17
