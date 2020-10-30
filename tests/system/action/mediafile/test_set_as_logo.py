from tests.system.action.base import BaseActionTestCase


class MediafileSetAsLogoActionTest(BaseActionTestCase):
    def test_set_as_logo_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_meeting222"})
        self.create_model(
            "mediafile/17",
            {"is_directory": False, "mimetype": "image/png", "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {"action": "mediafile.set_as_logo", "data": [{"id": 17, "place": "1"}]}
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("mediafile/17")
        assert model.get("used_as_logo_$1_in_meeting_id") == 222
        assert model.get("used_as_logo_$_in_meeting_id") == ["1"]

    def test_set_as_logo_wrong_directory(self) -> None:
        self.create_model("meeting/222", {"name": "name_meeting222"})
        self.create_model(
            "mediafile/17",
            {"is_directory": True, "mimetype": "image/png", "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {"action": "mediafile.set_as_logo", "data": [{"id": 17, "place": "1"}]}
            ],
        )
        self.assert_status_code(response, 400)
        assert "Cannot set a directory as logo." in str(response.data)

    def test_set_as_logo_wrong_no_image(self) -> None:
        self.create_model("meeting/222", {"name": "name_meeting222"})
        self.create_model(
            "mediafile/17",
            {"is_directory": False, "mimetype": "text/plain", "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {"action": "mediafile.set_as_logo", "data": [{"id": 17, "place": "1"}]}
            ],
        )
        self.assert_status_code(response, 400)
        assert "Cannot set a non image as logo." in str(response.data)
