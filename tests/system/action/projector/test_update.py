from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorUpdate(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_update_correct(self) -> None:
        self.set_models({"projector/2": {"meeting_id": 1}})
        response = self.request(
            "projector.update",
            {
                "id": 2,
                "name": "name_Xcdfgee",
                "is_internal": True,
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
                "chyron_background_color_2": "#ffffff",
                "chyron_font_color_2": "#ffffff",
                "show_header_footer": True,
                "show_title": True,
                "show_logo": True,
                "show_clock": True,
            },
        )
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "projector/2",
            {
                "name": "name_Xcdfgee",
                "width": 100,
                "aspect_ratio_numerator": 3,
                "aspect_ratio_denominator": 4,
            },
        )

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
            "is_internal",
            "show_header_footer",
            "show_title",
            "show_logo",
            "show_clock",
        ):
            assert model.get(bool_field) is True

    def test_update_wrong_id(self) -> None:
        response = self.request("projector.update", {"id": 2, "name": "name_Xcdfgee"})
        self.assert_status_code(response, 400)
        self.assert_model_exists("projector/1", {"name": None})

    def test_update_wrong_color(self) -> None:
        response = self.request("projector.update", {"id": 1, "color": "#aaaXbb"})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action projector.update: data.color must match pattern ^#[0-9a-fA-F]{6}$",
            response.json["message"],
        )

    def test_update_set_used_as_default_projector_in_meeting_id(self) -> None:
        response = self.request(
            "projector.update",
            {
                "id": 1,
                "used_as_default_projector_for_topic_in_meeting_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/1",
            {"used_as_default_projector_for_topic_in_meeting_id": 1},
        )
        self.assert_model_exists("meeting/1", {"default_projector_topic_ids": [1]})

    def test_update_add_used_as_default_projector_in_meeting_id(self) -> None:
        self.set_models(
            {
                "projector/1": {
                    "used_as_default_projector_for_topic_in_meeting_id": 1,
                },
                "projector/2": {"meeting_id": 1},
            }
        )
        response = self.request(
            "projector.update",
            {"id": 2, "used_as_default_projector_for_topic_in_meeting_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/1",
            {"used_as_default_projector_for_topic_in_meeting_id": 1},
        )
        self.assert_model_exists(
            "projector/2",
            {"used_as_default_projector_for_topic_in_meeting_id": 1},
        )
        self.assert_model_exists("meeting/1", {"default_projector_topic_ids": [1, 2]})

    def test_update_set_wrong_used_as_default_projector_in_meeting_id(self) -> None:
        response = self.request(
            "projector.update",
            {"id": 1, "used_as_default_xxxtopics_in_meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action projector.update: data must not contain {'used_as_default_xxxtopics_in_meeting_id'} properties",
            response.json["message"],
        )

    def test_update_reference_projector_internal_error(self) -> None:
        response = self.request("projector.update", {"id": 1, "is_internal": True})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Projector cannot be set to internal, because it is the reference projector of the meeting.",
            response.json["message"],
        )

    def test_update_reference_projector_internal_okay(self) -> None:
        response = self.request("projector.update", {"id": 1, "is_internal": False})
        self.assert_status_code(response, 200)

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.update",
            {
                "id": 1,
                "name": "name_Xcdfgee",
                "width": 100,
            },
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.update",
            {
                "id": 1,
                "name": "name_Xcdfgee",
                "width": 100,
            },
            Permissions.Projector.CAN_MANAGE,
        )

    def test_update_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.update",
            {
                "id": 1,
                "name": "name_Xcdfgee",
                "width": 100,
            },
        )
