from typing import Any

from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class MeetingSetLogoActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "name": "name_meeting1",
                "is_active_in_organization_id": 1,
                "meeting_mediafile_ids": [7],
            },
            "mediafile/17": {
                "is_directory": False,
                "mimetype": "image/png",
                "owner_id": "meeting/1",
                "meeting_mediafile_ids": [7],
            },
            "meeting_mediafile/7": {"meeting_id": 1, "mediafile_id": 17},
        }

    def test_set_logo_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                    "meeting_mediafile_ids": [7],
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": "meeting/222",
                    "meeting_mediafile_ids": [7],
                },
                "meeting_mediafile/7": {"meeting_id": 222, "mediafile_id": 17},
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/222", {"logo_web_header_id": 7})

    def test_set_logo_svg_xml(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                    "meeting_mediafile_ids": [7],
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/svg+xml",
                    "owner_id": "meeting/222",
                    "meeting_mediafile_ids": [7],
                },
                "meeting_mediafile/7": {"meeting_id": 222, "mediafile_id": 17},
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/222", {"logo_web_header_id": 7})

    def test_set_logo_wrong_place(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                    "meeting_mediafile_ids": [7],
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": "meeting/222",
                    "meeting_mediafile_ids": [7],
                },
                "meeting_mediafile/7": {"meeting_id": 222, "mediafile_id": 17},
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 222, "mediafile_id": 17, "place": "broken"}
        )
        self.assert_status_code(response, 400)
        assert (
            "logo_broken_id is not a valid field for model meeting."
            == response.json["message"]
        )

    def test_set_logo_wrong_directory(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                    "meeting_mediafile_ids": [7],
                },
                "mediafile/17": {
                    "is_directory": True,
                    "mimetype": "image/png",
                    "owner_id": "meeting/222",
                    "meeting_mediafile_ids": [7],
                },
                "meeting_mediafile/7": {"meeting_id": 222, "mediafile_id": 17},
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 400)
        assert "Cannot set a directory." in response.json["message"]

    def test_set_logo_wrong_no_image(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                    "meeting_mediafile_ids": [7],
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "text/plain",
                    "owner_id": "meeting/222",
                    "meeting_mediafile_ids": [7],
                },
                "meeting_mediafile/7": {"meeting_id": 222, "mediafile_id": 17},
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 400)
        assert "Invalid mimetype" in response.json["message"]

    def test_set_logo_orga_mediafile_error(self) -> None:
        self.create_meeting(1)
        self.set_models(
            {
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 1, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "No meeting_mediafile creation possible: Mediafile is not published.",
            response.json["message"],
        )

    def test_set_logo_published_root_orga_mediafile(self) -> None:
        self.create_meeting(1)
        self.set_models(
            {
                "meeting/1": {"meeting_mediafile_ids": [7]},
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "meeting_mediafile_ids": [7],
                },
                "meeting_mediafile/7": {
                    "meeting_id": 1,
                    "mediafile_id": 17,
                    "is_public": True,
                    "inherited_access_group_ids": [],
                },
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 1, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"logo_web_header_id": 7})

    def test_set_logo_published_root_orga_mediafile_generate_data(self) -> None:
        self.create_meeting(1)
        self.set_models(
            {
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 1, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"logo_web_header_id": 1})
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "meeting_id": 1,
                "mediafile_id": 17,
                "access_group_ids": [2],
                "inherited_access_group_ids": [2],
                "is_public": False,
            },
        )

    def test_set_logo_published_child_orga_mediafile_generate_data(self) -> None:
        self.create_meeting(1)
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
                    "mimetype": "image/png",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 1, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting/1", {"logo_web_header_id": 1})
        meeting_mediafile = self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "meeting_id": 1,
                "mediafile_id": 17,
                "inherited_access_group_ids": [2],
                "is_public": False,
            },
        )
        assert "access_group_ids" not in meeting_mediafile

    def test_set_logo_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.set_logo",
            {"id": 1, "mediafile_id": 17, "place": "web_header"},
        )

    def test_set_logo_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.set_logo",
            {"id": 1, "mediafile_id": 17, "place": "web_header"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )

    def test_set_logo_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "meeting.set_logo",
            {"id": 1, "mediafile_id": 17, "place": "web_header"},
        )
