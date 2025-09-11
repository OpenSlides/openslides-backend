from typing import Any

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class MeetingSetFontActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "mediafile/17": {
                "is_directory": False,
                "mimetype": "font/woff",
                "owner_id": "meeting/1",
            },
            "meeting_mediafile/7": {
                "meeting_id": 1,
                "mediafile_id": 17,
                "is_public": True,
            },
        }

    def test_set_font_correct(self) -> None:
        self.set_models(self.permission_test_models)
        response = self.request(
            "meeting.set_font", {"id": 1, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"font_bold_id": 7})
        self.assert_model_exists(
            "meeting_mediafile/7", {"used_as_font_bold_in_meeting_id": 1}
        )

    def test_set_font_wrong_place(self) -> None:
        self.set_models(self.permission_test_models)
        response = self.request(
            "meeting.set_font", {"id": 1, "mediafile_id": 17, "place": "broken"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "font_broken_id is not a valid field for model meeting.",
            response.json["message"],
        )

    def test_set_font_wrong_directory(self) -> None:
        self.permission_test_models["mediafile/17"] = {
            "owner_id": "meeting/1",
            "is_directory": True,
        }
        self.set_models(self.permission_test_models)
        response = self.request(
            "meeting.set_font", {"id": 1, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual("Cannot set a directory.", response.json["message"])

    def test_set_font_wrong_no_image(self) -> None:
        self.permission_test_models["mediafile/17"]["mimetype"] = "text/plain"
        self.set_models(self.permission_test_models)
        response = self.request(
            "meeting.set_font", {"id": 1, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Invalid mimetype: text/plain, allowed are ['font/ttf', 'font/woff', 'application/font-woff', 'application/font-sfnt']",
            response.json["message"],
        )

    def test_set_font_orga_mediafile_error(self) -> None:
        self.set_models(
            {
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "font/woff",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 1, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "No meeting_mediafile creation possible: Mediafile is not published.",
            response.json["message"],
        )

    def test_set_font_published_root_orga_mediafile(self) -> None:
        self.permission_test_models["mediafile/17"].update(
            {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            }
        )
        self.set_models(self.permission_test_models)
        response = self.request(
            "meeting.set_font", {"id": 1, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"font_bold_id": 7})
        self.assert_model_exists(
            "meeting_mediafile/7", {"used_as_font_bold_in_meeting_id": 1}
        )

    def test_set_font_published_root_orga_mediafile_generate_data(self) -> None:
        self.set_models(
            {
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "font/woff",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 1, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"font_bold_id": 1})
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "meeting_id": 1,
                "mediafile_id": 17,
                "access_group_ids": [2],
                "inherited_access_group_ids": [2],
                "is_public": False,
                "used_as_font_bold_in_meeting_id": 1,
            },
        )

    def test_set_font_published_child_orga_mediafile_generate_data(self) -> None:
        self.set_models(
            {
                "mediafile/16": {
                    "is_directory": True,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "child_ids": [17],
                },
                "mediafile/17": {
                    "parent_id": 16,
                    "is_directory": False,
                    "mimetype": "font/woff",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            }
        )
        response = self.request(
            "meeting.set_font", {"id": 1, "mediafile_id": 17, "place": "bold"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"font_bold_id": 1})
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "meeting_id": 1,
                "mediafile_id": 17,
                "access_group_ids": None,
                "inherited_access_group_ids": [2],
                "is_public": False,
                "used_as_font_bold_in_meeting_id": 1,
            },
        )

    def test_set_font_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.set_font",
            {"id": 1, "mediafile_id": 17, "place": "bold"},
        )

    def test_set_font_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.set_font",
            {"id": 1, "mediafile_id": 17, "place": "bold"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )

    def test_set_font_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "meeting.set_font",
            {"id": 1, "mediafile_id": 17, "place": "bold"},
        )
