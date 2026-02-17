from openslides_backend.models.models import Projector
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222)

    def test_create_correct_and_defaults(self) -> None:
        response = self.request(
            "projector.create", {"name": "test projector", "meeting_id": 222}
        )
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "projector/223",
            {"name": "test projector", "meeting_id": 222, "sequential_number": 2},
        )
        self.assert_defaults(Projector, model)

    def test_create_all_fields(self) -> None:
        data = {
            "name": "Test",
            "meeting_id": 222,
            "is_internal": True,
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
            "chyron_background_color_2": "#123456",
            "chyron_font_color_2": "#ffaaff",
            "show_header_footer": True,
            "show_title": True,
            "show_logo": True,
            "show_clock": True,
        }
        response = self.request("projector.create", data)
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector/223", data)

    def test_create_wrong_color(self) -> None:
        response = self.request(
            "projector.create",
            {"name": "Test", "meeting_id": 222, "color": "fg0000"},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action projector.create: data.color must match pattern ^#[0-9a-fA-F]{6}$",
            response.json["message"],
        )

    def test_create_wrong_width(self) -> None:
        response = self.request(
            "projector.create",
            {"name": "Test", "meeting_id": 222, "width": -2},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action projector.create: data.width must be bigger than or equal to 1",
            response.json["message"],
        )

    def test_create_set_used_as_default_in_meeting_id(self) -> None:
        response = self.request(
            "projector.create",
            {
                "name": "Test",
                "meeting_id": 222,
                "used_as_default_projector_for_topic_in_meeting_id": 222,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/223",
            {"used_as_default_projector_for_topic_in_meeting_id": 222},
        )
        self.assert_model_exists(
            "meeting/222", {"default_projector_topic_ids": [222, 223]}
        )

    def test_create_set_wrong_used_as_default__in_meeting_id(self) -> None:
        response = self.request(
            "projector.create",
            {
                "name": "Test",
                "meeting_id": 222,
                "used_as_default_xxxtopics_in_meeting_id": 222,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action projector.create: data must not contain {'used_as_default_xxxtopics_in_meeting_id'} properties",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.create",
            {"name": "test projector", "meeting_id": 1},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.create",
            {"name": "test projector", "meeting_id": 1},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_create_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.create",
            {"name": "test projector", "meeting_id": 1},
        )
