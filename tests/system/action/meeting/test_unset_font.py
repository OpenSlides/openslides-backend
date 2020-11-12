from tests.system.action.base import BaseActionTestCase


class MediafileUnsetFontActionTest(BaseActionTestCase):
    def test_unset_font(self) -> None:
        self.create_model(
            "meeting/222",
            {
                "name": "name_meeting222",
                "font_$header_id": 17,
                "font_$other_id": 17,
                "font_$_id": ["header", "other"],
            },
        )
        self.create_model(
            "mediafile/17",
            {
                "is_directory": False,
                "mimetype": "image/png",
                "meeting_id": 222,
                "used_as_font_$header_in_meeting_id": 222,
                "used_as_font_$other_in_meeting_id": 222,
                "used_as_font_$_in_meeting_id": ["header", "other"],
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.unset_font",
                    "data": [{"id": 222, "place": "header"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("font_$header_id") is None
        assert model.get("font_$other_id") == 17
        assert model.get("font_$_id") == ["other"]
