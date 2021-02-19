from tests.system.action.base import BaseActionTestCase


class ProjectorUpdate(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models({"projector/111": {"name": "name_srtgb123"}})
        response = self.request(
            "projector.update",
            {
                "id": 111,
                "name": "name_Xcdfgee",
                "width": 100,
                "aspect_ratio_numerator": 3,
                "aspect_ratio_denominator": 4,
                "color": "ffffff",
                "background_color": "ffffff",
                "header_background_color": "ffffff",
                "header_font_color": "ffffff",
                "header_h1_color": "ffffff",
                "chyron_background_color": "ffffff",
                "chyron_font_color": "ffffff",
                "show_header_footer": True,
                "show_title": True,
                "show_logo": True,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("projector/111")
        assert model.get("name") == "name_Xcdfgee"
        assert model.get("width") == 100
        assert model.get("aspect_ratio_numerator") == 3
        assert model.get("aspect_ratio_denominator") == 4

        for color_field in (
            "color",
            "background_color",
            "header_background_color",
            "header_font_color",
            "header_h1_color",
            "chyron_background_color",
            "chyron_font_color",
        ):
            assert model.get(color_field) == "ffffff"
        for bool_field in (
            "show_header_footer",
            "show_title",
            "show_logo",
        ):
            assert model.get(bool_field) is True

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {"projector/111": {"name": "name_srtgb123"}},
        )
        response = self.request("projector.update", {"id": 112, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 400)
        model = self.get_model("projector/111")
        assert model.get("name") == "name_srtgb123"
