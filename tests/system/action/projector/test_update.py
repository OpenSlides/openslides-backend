from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorUpdate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "projector/111": {"name": "name_srtgb123", "meeting_id": 1},
        }

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "projector/111": {"name": "name_srtgb123", "meeting_id": 1},
            }
        )
        response = self.request(
            "projector.update",
            {
                "id": 111,
                "name": "name_Xcdfgee",
                "width": 100,
                "aspect_ratio_numerator": 3,
                "aspect_ratio_denominator": 4,
                "color": "#ffffff",
                "background_color": "#ffffff",
                "header_background_color": "#ffffff",
                "header_font_color": "#ffffff",
                "header_h1_color": "#ffffff",
                "chyron_background_color": "#ffffff",
                "chyron_font_color": "#ffffff",
                "show_header_footer": True,
                "show_title": True,
                "show_logo": True,
                "show_clock": True,
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
            assert model.get(color_field) == "#ffffff"
        for bool_field in (
            "show_header_footer",
            "show_title",
            "show_logo",
            "show_clock",
        ):
            assert model.get(bool_field) is True

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "projector/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
        )
        response = self.request("projector.update", {"id": 112, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 400)
        model = self.get_model("projector/111")
        assert model.get("name") == "name_srtgb123"

    def test_update_wrong_color(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "projector/111": {"name": "name_srtgb123", "meeting_id": 1},
            },
        )
        response = self.request("projector.update", {"id": 112, "color": "#aaaXbb"})
        self.assert_status_code(response, 400)
        assert (
            "data.color must match pattern ^#[0-9a-f]{6}$" in response.json["message"]
        )

    def test_update_set_used_as_default__in_meeting_id(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "projector_ids": [1],
                    "is_active_in_organization_id": 1,
                },
                "projector/1": {"name": "Projector1", "meeting_id": 222},
            }
        )
        response = self.request(
            "projector.update",
            {
                "id": 1,
                "used_as_default_$_in_meeting_id": {"topics": 222},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/1",
            {
                "used_as_default_$_in_meeting_id": ["topics"],
                "used_as_default_$topics_in_meeting_id": 222,
            },
        )
        self.assert_model_exists(
            "meeting/222",
            {"default_projector_$_id": ["topics"], "default_projector_$topics_id": 1},
        )

    def test_update_not_allowed_change_used_as_default__in_meeting_id(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "projector_ids": [1],
                    "default_projector_$_id": ["topics"],
                    "default_projector_$topics_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "projector/1": {
                    "name": "Projector1",
                    "meeting_id": 222,
                    "used_as_default_$_in_meeting_id": ["topics"],
                    "used_as_default_$topics_in_meeting_id": 222,
                },
                "projector/2": {"name": "Projector2", "meeting_id": 222},
            }
        )
        response = self.request(
            "projector.update",
            {
                "id": 2,
                "used_as_default_$_in_meeting_id": {"topics": 222},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/1",
            {
                "used_as_default_$_in_meeting_id": [],
                "used_as_default_$topics_in_meeting_id": None,
            },
        )
        self.assert_model_exists(
            "projector/2",
            {
                "used_as_default_$_in_meeting_id": ["topics"],
                "used_as_default_$topics_in_meeting_id": 222,
            },
        )
        self.assert_model_exists(
            "meeting/222",
            {"default_projector_$_id": ["topics"], "default_projector_$topics_id": 2},
        )

    def test_update_change_used_as_default__in_meeting_id(self) -> None:
        """
        To really change the value, it must be first set to None and in next
        action/request can be set to a new value
        """
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "projector_ids": [1],
                    "default_projector_$_id": ["topics"],
                    "default_projector_$topics_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "projector/1": {
                    "name": "Projector1",
                    "meeting_id": 222,
                    "used_as_default_$_in_meeting_id": ["topics"],
                    "used_as_default_$topics_in_meeting_id": 222,
                },
                "projector/2": {"name": "Projector2", "meeting_id": 222},
            }
        )
        response = self.request(
            "projector.update",
            {
                "id": 1,
                "used_as_default_$_in_meeting_id": {"topics": None},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/1",
            {
                "used_as_default_$_in_meeting_id": [],
                "used_as_default_$topics_in_meeting_id": None,
            },
        )
        self.assert_model_exists(
            "meeting/222",
            {"default_projector_$_id": [], "default_projector_$topics_id": None},
        )

        response = self.request(
            "projector.update",
            {
                "id": 2,
                "used_as_default_$_in_meeting_id": {"topics": 222},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/1",
            {
                "used_as_default_$_in_meeting_id": [],
                "used_as_default_$topics_in_meeting_id": None,
            },
        )
        self.assert_model_exists(
            "projector/2",
            {
                "used_as_default_$_in_meeting_id": ["topics"],
                "used_as_default_$topics_in_meeting_id": 222,
            },
        )
        self.assert_model_exists(
            "meeting/222",
            {"default_projector_$_id": ["topics"], "default_projector_$topics_id": 2},
        )

    def test_update_set_wrong_used_as_default__in_meeting_id(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "projector_ids": [1],
                    "is_active_in_organization_id": 1,
                },
                "projector/1": {"name": "Projector1", "meeting_id": 222},
            }
        )
        response = self.request(
            "projector.update",
            {
                "id": 1,
                "used_as_default_$_in_meeting_id": {"xxxtopics": 222},
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.used_as_default_$_in_meeting_id must not contain {'xxxtopics'} properties",
            response.json["message"],
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "projector.update",
            {
                "id": 111,
                "name": "name_Xcdfgee",
                "width": 100,
            },
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "projector.update",
            {
                "id": 111,
                "name": "name_Xcdfgee",
                "width": 100,
            },
            Permissions.Projector.CAN_MANAGE,
        )
