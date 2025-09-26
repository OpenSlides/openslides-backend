from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MediafileUnsetFontActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"font_projector_h1_id": 7, "font_projector_h2_id": 7},
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/7": {
                    "meeting_id": 1,
                    "mediafile_id": 17,
                    "is_public": True,
                },
            }
        )

    def test_unset_font(self) -> None:
        response = self.request(
            "meeting.unset_font", {"id": 1, "place": "projector_h1"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"font_projector_h1_id": None, "font_projector_h2_id": 7}
        )
        self.assert_model_exists(
            "meeting_mediafile/7",
            {
                "used_as_font_projector_h1_in_meeting_id": None,
                "used_as_font_projector_h2_in_meeting_id": 1,
            },
        )

    def test_unset_font_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "meeting.unset_font",
            {"id": 1, "place": "bold"},
        )

    def test_unset_font_permissions(self) -> None:
        self.base_permission_test(
            {},
            "meeting.unset_font",
            {"id": 1, "place": "bold"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )

    def test_unset_font_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "meeting.unset_font",
            {"id": 1, "place": "bold"},
        )
