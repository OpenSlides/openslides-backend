from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MediafileUnsetFontActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "name": "name_meeting1",
                "font_projector_h1_id": 7,
                "font_projector_h2_id": 7,
                "is_active_in_organization_id": 1,
                "meeting_mediafile_ids": [7],
            },
            "mediafile/17": {
                "is_directory": False,
                "mimetype": "image/png",
                "owner_id": "meeting/1",
                "meeting_mediafile_ids": [7],
            },
            "meeting_mediafile/7": {
                "meeting_id": 1,
                "mediafile_id": 17,
                "used_as_font_projector_h1_in_meeting_id": 1,
                "used_as_font_projector_h2_in_meeting_id": 1,
            },
        }

    def test_unset_font(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "font_projector_h1_id": 7,
                    "font_projector_h2_id": 7,
                    "is_active_in_organization_id": 1,
                    "meeting_mediafile_ids": [7],
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": "meeting/222",
                    "meeting_mediafile_ids": [7],
                },
                "meeting_mediafile/7": {
                    "meeting_id": 222,
                    "mediafile_id": 17,
                    "used_as_font_projector_h1_in_meeting_id": 222,
                    "used_as_font_projector_h2_in_meeting_id": 222,
                },
            }
        )
        response = self.request(
            "meeting.unset_font", {"id": 222, "place": "projector_h1"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("font_projector_h1_id") is None
        assert model.get("font_projector_h2_id") == 7

    def test_unset_font_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.unset_font",
            {"id": 1, "place": "bold"},
        )

    def test_unset_font_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.unset_font",
            {"id": 1, "place": "bold"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )

    def test_unset_font_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "meeting.unset_font",
            {"id": 1, "place": "bold"},
        )
