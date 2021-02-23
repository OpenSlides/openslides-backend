from openslides_backend.models.models import Projector
from tests.system.action.base import BaseActionTestCase


class ProjectorCreateActionTest(BaseActionTestCase):
    def test_create_correct_and_defaults(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
            }
        )
        response = self.request(
            "projector.create",
            {
                "name": "test projector",
                "meeting_id": 222,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/1", {"name": "test projector", "meeting_id": 222}
        )
        model = self.get_model("projector/1")
        self.assert_defaults(Projector, model)

    def test_create_all_fields(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
            }
        )
        data = {
            "name": "Test",
            "meeting_id": 222,
            "width": 100,
            "aspect_ratio_numerator": 101,
            "aspect_ratio_denominator": 102,
            "color": "#ff0000",
            "background_color": "#036aee",
            "header_background_color": "#123456",
            "header_font_color": "#7890ab",
            "header_h1_color": "#cdef01",
            "chyron_background_color": "#234567",
            "chyron_font_color": "#890abc",
            "show_header_footer": True,
            "show_title": True,
            "show_logo": True,
            "show_clock": True,
        }
        response = self.request("projector.create", data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector/1", data)

    def test_create_wrong_color(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        response = self.request(
            "projector.create",
            {
                "name": "Test",
                "meeting_id": 222,
                "color": "fg0000",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.color must match pattern",
            response.json["message"],
        )

    def test_create_wrong_width(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        response = self.request(
            "projector.create",
            {
                "name": "Test",
                "meeting_id": 222,
                "width": -2,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.width must be bigger than or equal to 1",
            response.json["message"],
        )
