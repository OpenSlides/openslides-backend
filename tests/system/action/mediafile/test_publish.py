from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class MediafileUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.orga_permission_test_models: dict[str, dict[str, Any]] = {
            "mediafile/111": {
                "title": "title_srtgb123",
                "owner_id": ONE_ORGANIZATION_FQID,
            },
        }
        self.test_models: dict[str, dict[str, Any]] = {
            "mediafile/110": {
                "title": "title_srtgb199",
                "child_ids": [111],
                "is_directory": True,
                "owner_id": ONE_ORGANIZATION_FQID,
            },
            "mediafile/111": {
                "title": "title_srtgb123",
                "parent_id": 110,
                "is_directory": True,
                "owner_id": ONE_ORGANIZATION_FQID,
            },
            "mediafile/112": {
                "title": "title_srtgb123",
                "parent_id": 111,
                "owner_id": ONE_ORGANIZATION_FQID,
            },
            "mediafile/113": {
                "title": "title_srtgb123",
                "parent_id": 111,
                "owner_id": ONE_ORGANIZATION_FQID,
            },
        }
        self.published_update_data: dict[str, dict[str, Any]] = {
            "group/1": {
                "meeting_mediafile_access_group_ids": [1113],
                "meeting_mediafile_inherited_access_group_ids": [1113],
            },
            "mediafile/110": {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
            "mediafile/111": {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
            "mediafile/112": {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
            "mediafile/113": {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
            "meeting_mediafile/1110": {
                "mediafile_id": 110,
                "meeting_id": 1,
                "is_public": True,
            },
            "meeting_mediafile/1111": {
                "mediafile_id": 111,
                "meeting_id": 1,
                "is_public": True,
            },
            "meeting_mediafile/1112": {
                "mediafile_id": 112,
                "meeting_id": 1,
                "is_public": True,
            },
            "meeting_mediafile/1113": {
                "mediafile_id": 113,
                "meeting_id": 1,
                "is_public": False,
            },
        }

    def test_publish(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "mediafile.publish",
            {"id": 110, "publish": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/1",
            {
                "meeting_mediafile_access_group_ids": None,
                "meeting_mediafile_inherited_access_group_ids": None,
            },
        )
        self.assert_model_not_exists("meeting_mediafile/1110")
        for id_ in [110, 111, 112, 113]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            )

    def test_publish_published_file(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 110, "publish": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/1",
            {
                "meeting_mediafile_access_group_ids": [1113],
                "meeting_mediafile_inherited_access_group_ids": [1113],
            },
        )
        for id_ in [110, 111, 112, 113]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            )
            self.assert_model_exists(f"meeting_mediafile/1{id_}", {"mediafile_id": id_})

    def test_publish_non_top_level_file(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "mediafile.publish",
            {"id": 111, "publish": True},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Only top-level mediafiles may be published",
            response.json["message"],
        )

    def test_publish_implicitly_published_file(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 112, "publish": True},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Only top-level mediafiles may be published",
            response.json["message"],
        )

    def test_unpublish(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 110, "publish": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/1",
            {
                "meeting_mediafile_access_group_ids": None,
                "meeting_mediafile_inherited_access_group_ids": None,
            },
        )
        for id_ in [110, 111, 112, 113]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "published_to_meetings_in_organization_id": None,
                },
            )
            self.assert_model_not_exists(f"meeting_mediafile/1{id_}")

    def test_publish_wrong_payload(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 110, "publish": None},
        )
        self.assert_status_code(response, 400)
        self.assertIn("data.publish must be boolean", response.json["message"])

    def test_unpublish_implicitly_published(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 111, "publish": False},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Only top-level mediafiles may be published",
            response.json["message"],
        )

    def test_publish_single_mediafile(self) -> None:
        self.set_models(
            {
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
            }
        )
        response = self.request(
            "mediafile.publish",
            {"id": 111, "publish": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/111",
            {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )

    def test_publish_meeting_mediafile(self) -> None:
        self.set_models(
            {
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/1111": {
                    "mediafile_id": 111,
                    "is_public": True,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "mediafile.publish",
            {"id": 111, "publish": True},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Only organization-owned mediafiles may be published",
            response.json["message"],
        )

    def test_publish_no_permissions_orga_owner(self) -> None:
        self.base_permission_test(
            self.orga_permission_test_models,
            "mediafile.publish",
            {"id": 111, "publish": True},
        )

    def test_publish_permissions_orga_owner(self) -> None:
        self.base_permission_test(
            self.orga_permission_test_models,
            "mediafile.publish",
            {"id": 111, "publish": False},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
