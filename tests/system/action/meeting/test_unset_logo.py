from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MediafileUnsetLogoActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "logo_pdf_header_l_id": 7,
                "logo_pdf_header_r_id": 7,
            },
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

    def test_unset_logo(self) -> None:
        self.set_models(self.permission_test_models)
        response = self.request(
            "meeting.unset_logo", {"id": 1, "place": "pdf_header_l"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"logo_pdf_header_l_id": None, "logo_pdf_header_r_id": 7}
        )
        self.assert_model_exists(
            "meeting_mediafile/7",
            {
                "used_as_logo_pdf_header_l_in_meeting_id": None,
                "used_as_logo_pdf_header_r_in_meeting_id": 1,
            },
        )

    def test_unset_with_underscore(self) -> None:
        self.permission_test_models["meeting/1"]["logo_web_header_id"] = 7
        self.set_models(self.permission_test_models)
        response = self.request("meeting.unset_logo", {"id": 1, "place": "web_header"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"logo_web_header_id": None})
        self.assert_model_exists(
            "meeting_mediafile/7",
            {
                "used_as_logo_web_header_in_meeting_id": None,
                "used_as_logo_pdf_header_l_in_meeting_id": 1,
                "used_as_logo_pdf_header_r_in_meeting_id": 1,
            },
        )

    def test_unset_logo_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.unset_logo",
            {"id": 1, "place": "web_header"},
        )

    def test_unset_logo_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.unset_logo",
            {"id": 1, "place": "web_header"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )

    def test_unset_logo_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "meeting.unset_logo",
            {"id": 1, "place": "web_header"},
        )
