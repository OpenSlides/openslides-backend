from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MediafileMoveActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "mediafile/7": {"owner_id": "meeting/1", "is_directory": True},
            "mediafile/8": {"owner_id": "meeting/1", "is_directory": True},
        }

    def test_move_parent_none(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/7": {
                    "title": "title_7",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [8, 9],
                },
                "mediafile/8": {
                    "title": "title_8",
                    "owner_id": "meeting/222",
                    "parent_id": 7,
                    "child_ids": [],
                },
                "mediafile/9": {
                    "title": "title_9",
                    "owner_id": "meeting/222",
                    "parent_id": 7,
                    "child_ids": [10],
                },
                "mediafile/10": {
                    "title": "title_10",
                    "owner_id": "meeting/222",
                    "parent_id": 9,
                    "child_ids": [],
                },
            }
        )
        response = self.request(
            "mediafile.move",
            {"owner_id": "meeting/222", "ids": [8, 9], "parent_id": None},
        )
        self.assert_status_code(response, 200)
        mediafile_7 = self.get_model("mediafile/7")
        assert mediafile_7.get("child_ids") == []
        assert mediafile_7.get("parent_id") is None
        mediafile_8 = self.get_model("mediafile/8")
        assert mediafile_8.get("child_ids") == []
        assert mediafile_8.get("parent_id") is None
        assert mediafile_8.get("is_public")
        mediafile_9 = self.get_model("mediafile/9")
        assert mediafile_9.get("child_ids") == [10]
        assert mediafile_9.get("parent_id") is None
        assert mediafile_9.get("is_public")
        mediafile_10 = self.get_model("mediafile/10")
        assert mediafile_10.get("is_public")
        assert mediafile_10.get("inherited_access_group_ids") == []

    def test_move_parent_set(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/7": {
                    "title": "title_7",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                    "is_directory": True,
                    "is_public": True,
                    "inherited_access_group_ids": [],
                },
                "mediafile/8": {
                    "title": "title_8",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                },
                "mediafile/9": {
                    "title": "title_9",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                },
            }
        )
        response = self.request(
            "mediafile.move", {"owner_id": "meeting/222", "ids": [8, 9], "parent_id": 7}
        )
        self.assert_status_code(response, 200)
        mediafile_7 = self.get_model("mediafile/7")
        assert mediafile_7.get("child_ids") == [8, 9]
        assert mediafile_7.get("parent_id") is None
        mediafile_8 = self.get_model("mediafile/8")
        assert mediafile_8.get("child_ids") == []
        assert mediafile_8.get("parent_id") == 7
        assert mediafile_8.get("inherited_access_group_ids") == []
        assert mediafile_8.get("is_public")
        mediafile_9 = self.get_model("mediafile/9")
        assert mediafile_9.get("child_ids") == []
        assert mediafile_9.get("parent_id") == 7
        assert mediafile_9.get("is_public")
        assert mediafile_9.get("inherited_access_group_ids") == []

    def test_move_non_directory_parent_set(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/7": {
                    "title": "title_7",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                    "is_directory": False,
                },
                "mediafile/8": {
                    "title": "title_8",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                },
                "mediafile/9": {
                    "title": "title_9",
                    "owner_id": "meeting/222",
                    "parent_id": None,
                    "child_ids": [],
                },
            }
        )
        response = self.request(
            "mediafile.move", {"owner_id": "meeting/222", "ids": [8, 9], "parent_id": 7}
        )
        self.assert_status_code(response, 400)
        self.assertIn("Parent is not a directory.", response.json["message"])

    def test_move_multiple_action_data_items(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "mediafile/7": {"owner_id": "meeting/222", "is_directory": True},
                "mediafile/8": {"owner_id": "meeting/222", "is_directory": True},
            }
        )
        response = self.request_multi(
            "mediafile.move",
            [
                {"owner_id": "meeting/222", "ids": [8], "parent_id": 7},
                {"owner_id": "meeting/222", "ids": [7], "parent_id": 8},
            ],
        )
        self.assert_status_code(response, 400)
        mediafile_7 = self.get_model("mediafile/7")
        assert mediafile_7.get("parent_id") is None
        mediafile_8 = self.get_model("mediafile/8")
        assert mediafile_8.get("parent_id") is None

    def test_move_owner_mismatch(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "mediafile/7": {"owner_id": "meeting/222", "is_directory": True},
                "mediafile/8": {"owner_id": "meeting/222", "is_directory": True},
            }
        )
        response = self.request_multi(
            "mediafile.move",
            [
                {"owner_id": ONE_ORGANIZATION_FQID, "ids": [8], "parent_id": 7},
            ],
        )
        self.assert_status_code(response, 400)
        assert "Owner and parent don't match." in response.json["message"]

    def test_move_circle(self) -> None:
        self.set_models(
            {
                "meeting/222": {"is_active_in_organization_id": 1},
                "mediafile/7": {
                    "owner_id": "meeting/222",
                    "is_directory": True,
                    "child_ids": [8],
                },
                "mediafile/8": {
                    "owner_id": "meeting/222",
                    "is_directory": True,
                    "parent_id": 7,
                },
            }
        )
        response = self.request(
            "mediafile.move", {"owner_id": "meeting/222", "ids": [7], "parent_id": 8}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Moving item 7 to one of its children is not possible.",
            response.json["message"],
        )

    def test_move_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.move",
            {"owner_id": "meeting/1", "ids": [8], "parent_id": 7},
        )

    def test_move_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.move",
            {"owner_id": "meeting/1", "ids": [8], "parent_id": 7},
            Permissions.Mediafile.CAN_MANAGE,
        )

    def test_move_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "mediafile.move",
            {"owner_id": "meeting/1", "ids": [8], "parent_id": 7},
        )

    def test_move_no_permissions_orga(self) -> None:
        self.permission_test_models["mediafile/7"]["owner_id"] = ONE_ORGANIZATION_FQID
        self.permission_test_models["mediafile/8"]["owner_id"] = ONE_ORGANIZATION_FQID
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [8], "parent_id": 7},
        )

    def test_move_permissions_orga(self) -> None:
        self.permission_test_models["mediafile/7"]["owner_id"] = ONE_ORGANIZATION_FQID
        self.permission_test_models["mediafile/8"]["owner_id"] = ONE_ORGANIZATION_FQID
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.move",
            {"owner_id": ONE_ORGANIZATION_FQID, "ids": [8], "parent_id": 7},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
