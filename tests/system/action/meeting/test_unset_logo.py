from tests.system.action.base import BaseActionTestCase


class MediafileUnsetLogoActionTest(BaseActionTestCase):
    def test_unset_logo(self) -> None:
        self.create_model(
            "meeting/222",
            {
                "name": "name_meeting222",
                "logo_$place_id": 17,
                "logo_$other_id": 17,
                "logo_$_id": ["place", "other"],
            },
        )
        self.create_model(
            "mediafile/17",
            {"is_directory": False, "mimetype": "image/png", "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.unset_logo",
                    "data": [{"id": 222, "place": "place"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("logo_$place_id") is None
        assert model.get("logo_$other_id") == 17
        assert model.get("logo_$_id") == ["other"]

    def test_unset_with_underscore(self) -> None:
        self.create_model(
            "meeting/222",
            {
                "name": "name_meeting222",
                "logo_$web_header_id": 17,
                "logo_$_id": ["web_header"],
            },
        )
        self.create_model(
            "mediafile/17",
            {"is_directory": False, "mimetype": "image/png", "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.unset_logo",
                    "data": [{"id": 222, "place": "web_header"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("logo_$web_header_id") is None
        assert model.get("logo_$_id") == []
