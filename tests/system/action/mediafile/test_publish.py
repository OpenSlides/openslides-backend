from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase


class MediafileUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.orga_permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"name": "meeting_1", "is_active_in_organization_id": 1},
            "group/7": {
                "name": "group_LxAHErRs",
                "meeting_user_ids": [],
                "meeting_id": 1,
            },
            "mediafile/111": {
                "title": "title_srtgb123",
                "owner_id": ONE_ORGANIZATION_FQID,
            },
        }
        self.test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {"is_active_in_organization_id": 1},
            "group/7": {
                "name": "group_1",
                "meeting_user_ids": [],
                "meeting_id": 1,
            },
            "group/8": {
                "name": "group_2",
                "meeting_user_ids": [],
                "meeting_id": 1,
            },
            "mediafile/110": {
                "title": "title_srtgb199",
                "child_ids": [111],
                "is_directory": True,
                "owner_id": ONE_ORGANIZATION_FQID,
            },
            "mediafile/111": {
                "title": "title_srtgb123",
                "parent_id": 110,
                "child_ids": [112, 113],
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
            "meeting/1": {"meeting_mediafile_ids": [1110, 1111, 1112, 1113]},
            "group/7": {
                "mediafile_access_group_ids": [1113],
                "mediafile_inherited_access_group_ids": [1113],
            },
            "mediafile/110": {
                "is_published_to_meetings": True,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "meeting_mediafile_ids": [1110],
            },
            "mediafile/111": {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "meeting_mediafile_ids": [1111],
            },
            "mediafile/112": {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "meeting_mediafile_ids": [1112],
            },
            "mediafile/113": {
                "is_published_to_meetings": True,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "meeting_mediafile_ids": [1113],
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
                "access_group_ids": [7],
                "inherited_access_group_ids": [7],
            },
        }

    def test_publish(self) -> None:
        self.set_models(self.test_models)
        response = self.request(
            "mediafile.publish",
            {"id": 110, "is_published_to_meetings": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/7",
            {
                "mediafile_access_group_ids": None,
                "mediafile_inherited_access_group_ids": None,
            },
        )
        self.assert_model_not_exists("meeting_mediafile/1110")
        self.assert_model_exists(
            "mediafile/110",
            {
                "is_published_to_meetings": True,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )
        for id_ in [111, 112, 113]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "is_published_to_meetings": None,
                },
            )

    def test_publish_published_file(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 110, "is_published_to_meetings": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/7",
            {
                "mediafile_access_group_ids": [1113],
                "mediafile_inherited_access_group_ids": [1113],
            },
        )
        for id_ in [110, 111, 112, 113]:
            self.assert_model_exists(f"meeting_mediafile/1{id_}", {"mediafile_id": id_})
        self.assert_model_exists(
            "mediafile/110",
            {
                "is_published_to_meetings": True,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )
        for id_ in [111, 112]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "is_published_to_meetings": None,
                },
            )
        self.assert_model_exists(
            "mediafile/113",
            {
                "is_published_to_meetings": True,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )

    def test_publish_implicitly_published_file(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 112, "is_published_to_meetings": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/7",
            {
                "mediafile_access_group_ids": [1113],
                "mediafile_inherited_access_group_ids": [1113],
            },
        )
        for id_ in [110, 111, 112, 113]:
            self.assert_model_exists(f"meeting_mediafile/1{id_}", {"mediafile_id": id_})
        for id_ in [110, 112, 113]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "is_published_to_meetings": True,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            )
        self.assert_model_exists(
            "mediafile/111",
            {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "is_published_to_meetings": None,
            },
        )

    def test_unpublish(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 110, "is_published_to_meetings": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/7",
            {
                "mediafile_access_group_ids": [1113],
                "mediafile_inherited_access_group_ids": [1113],
            },
        )
        self.assert_model_exists(
            "mediafile/110",
            {
                "is_published_to_meetings": False,
                "published_to_meetings_in_organization_id": None,
            },
        )
        for id_ in [1110, 1111, 1112]:
            self.assert_model_deleted(f"meeting_mediafile/{id_}")
        for id_ in [111, 112]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "published_to_meetings_in_organization_id": None,
                    "is_published_to_meetings": None,
                },
            )
        self.assert_model_exists("meeting_mediafile/1113", {"mediafile_id": 113})
        self.assert_model_exists(
            "mediafile/113",
            {
                "is_published_to_meetings": True,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )

    def test_unpublish_with_parent_inheritance(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 113, "is_published_to_meetings": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/7",
            {
                "mediafile_access_group_ids": [1113],
                "mediafile_inherited_access_group_ids": [1113],
            },
        )
        self.assert_model_exists(
            "mediafile/110",
            {
                "is_published_to_meetings": True,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )
        self.assert_model_exists("meeting_mediafile/1110")
        for id_ in [111, 112]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    "is_published_to_meetings": None,
                },
            )
            self.assert_model_exists(f"meeting_mediafile/1{id_}")
        self.assert_model_exists(
            "mediafile/113",
            {
                "is_published_to_meetings": False,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            },
        )
        self.assert_model_exists("meeting_mediafile/1113")
        response = self.request(
            "mediafile.publish",
            {"id": 110, "is_published_to_meetings": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/7",
            {
                "mediafile_access_group_ids": [],
                "mediafile_inherited_access_group_ids": [],
            },
        )
        for id_ in [110, 113]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "published_to_meetings_in_organization_id": None,
                    "is_published_to_meetings": False,
                },
            )
        for id_ in [111, 112]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "published_to_meetings_in_organization_id": None,
                    "is_published_to_meetings": None,
                },
            )
        for id_ in [1110, 1111, 1112, 1113]:
            self.assert_model_deleted(f"meeting_mediafile/{id_}")

    def test_unpublish_implicitly_published(self) -> None:
        self.set_models(self.test_models)
        self.set_models(self.published_update_data)
        response = self.request(
            "mediafile.publish",
            {"id": 111, "is_published_to_meetings": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "group/7",
            {
                "mediafile_access_group_ids": [1113],
                "mediafile_inherited_access_group_ids": [1113],
            },
        )
        for id_ in [110, 113]:
            self.assert_model_exists(
                f"mediafile/{id_}",
                {
                    "is_published_to_meetings": True,
                    "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                },
            )
        self.assert_model_exists(
            "mediafile/111",
            {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "is_published_to_meetings": False,
            },
        )
        self.assert_model_exists(
            "mediafile/112",
            {
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                "is_published_to_meetings": None,
            },
        )
        for id_ in [1110, 1111, 1112, 1113]:
            self.assert_model_exists(f"meeting_mediafile/{id_}")

    def test_publish_meeting_mediafile(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "is_active_in_organization_id": 1,
                    "meeting_mediafile_ids": [1111],
                },
                "group/7": {
                    "name": "group_LxAHErRs",
                    "meeting_user_ids": [],
                    "meeting_id": 1,
                },
                "mediafile/111": {
                    "title": "title_srtgb123",
                    "owner_id": "meeting/1",
                    "meeting_mediafile_ids": [1111],
                },
                "meeting_mediafile/1111": {"mediafile_id": 111, "meeting_id": 1},
            }
        )
        response = self.request(
            "mediafile.publish",
            {"id": 111, "is_published_to_meetings": True},
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
            {"id": 111, "is_published_to_meetings": True},
        )

    def test_publish_permissions_orga_owner(self) -> None:
        self.base_permission_test(
            self.orga_permission_test_models,
            "mediafile.publish",
            {"id": 111, "is_published_to_meetings": False},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
