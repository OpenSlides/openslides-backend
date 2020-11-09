from tests.system.action.base import BaseActionTestCase


class MediafileUnsetLogoActionTest(BaseActionTestCase):
    def test_unset_logo(self) -> None:
        self.create_model(
            "meeting/222",
            {"name": "name_meeting222", "logo_$1_id": 17, "logo_$2_id": 17},
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
                    "data": [{"id": 222, "place": "2"}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("logo_$2_id") is None
        assert model.get("logo_$1_id") == 17
