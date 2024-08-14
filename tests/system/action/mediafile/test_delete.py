from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class MediafileDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "logo_web_header_id": 222,
                "is_active_in_organization_id": 1,
            },
            "mediafile/222": {
                "used_as_logo_web_header_in_meeting_id": 111,
                "owner_id": "meeting/1",
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/34": {"is_active_in_organization_id": 1},
                "mediafile/111": {"title": "title_srtgb123", "owner_id": "meeting/34"},
            }
        )
        response = self.request("mediafile.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/111")
        assert response.json["results"] == [None]

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/34": {"is_active_in_organization_id": 1},
                "mediafile/112": {"title": "title_srtgb123", "owner_id": "meeting/34"},
            }
        )
        response = self.request("mediafile.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("mediafile/112")
        assert model.get("title") == "title_srtgb123"

    def test_delete_directory(self) -> None:
        self.set_models(
            {
                "meeting/34": {"is_active_in_organization_id": 1},
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "is_directory": True,
                    "child_ids": [110],
                    "owner_id": "meeting/34",
                },
                "mediafile/110": {
                    "title": "title_ghjeu212",
                    "is_directory": False,
                    "parent_id": 112,
                    "owner_id": "meeting/34",
                },
            }
        )
        response = self.request("mediafile.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")

    def test_delete_directory_list_of_children(self) -> None:
        self.set_models(
            {
                "meeting/34": {"is_active_in_organization_id": 1},
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "is_directory": True,
                    "child_ids": [110],
                    "owner_id": "meeting/34",
                },
                "mediafile/110": {
                    "title": "title_ghjeu212",
                    "is_directory": True,
                    "child_ids": [113],
                    "parent_id": 112,
                    "owner_id": "meeting/34",
                },
                "mediafile/113": {
                    "title": "title_del2",
                    "is_directory": False,
                    "child_ids": [],
                    "parent_id": 110,
                    "owner_id": "meeting/34",
                },
            }
        )
        response = self.request("mediafile.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")
        self.assert_model_deleted("mediafile/113")

    def test_delete_directory_two_children(self) -> None:
        self.set_models(
            {
                "meeting/34": {"is_active_in_organization_id": 1},
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "is_directory": True,
                    "child_ids": [110, 113],
                    "owner_id": "meeting/34",
                },
                "mediafile/110": {
                    "title": "title_ghjeu212",
                    "is_directory": False,
                    "child_ids": [],
                    "parent_id": 112,
                    "owner_id": "meeting/34",
                },
                "mediafile/113": {
                    "title": "title_del2",
                    "is_directory": False,
                    "child_ids": [],
                    "parent_id": 112,
                    "owner_id": "meeting/34",
                },
            }
        )
        response = self.request("mediafile.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")
        self.assert_model_deleted("mediafile/113")

    def test_delete_check_relations(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "logo_web_header_id": 222,
                    "all_projection_ids": [1],
                    "is_active_in_organization_id": 1,
                },
                "mediafile/222": {
                    "used_as_logo_web_header_in_meeting_id": 111,
                    "projection_ids": [1],
                    "owner_id": "meeting/111",
                },
                "projection/1": {
                    "content_object_id": "mediafile/222",
                    "current_projector_id": 1,
                    "meeting_id": 111,
                },
                "projector/1": {
                    "current_projection_ids": [1],
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("mediafile.delete", {"id": 222})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/222")
        self.assert_model_deleted("projection/1")
        meeting = self.get_model("meeting/111")
        assert meeting.get("logo_web_header_id") is None

    def test_delete_directory_two_children_orga_owner(self) -> None:
        self.set_models(
            {
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "is_directory": True,
                    "child_ids": [110, 113],
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "mediafile/110": {
                    "title": "title_ghjeu212",
                    "is_directory": False,
                    "child_ids": [],
                    "parent_id": 112,
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "mediafile/113": {
                    "title": "title_del2",
                    "is_directory": False,
                    "child_ids": [],
                    "parent_id": 112,
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
            }
        )
        response = self.request("mediafile.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")
        self.assert_model_deleted("mediafile/113")

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.delete",
            {"id": 222},
        )

    def test_delete_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.delete",
            {"id": 222},
            Permissions.Mediafile.CAN_MANAGE,
        )

    def test_delete_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "mediafile.delete",
            {"id": 222},
        )

    def test_delete_orga_no_permissions(self) -> None:
        self.permission_test_models["mediafile/222"]["owner_id"] = ONE_ORGANIZATION_FQID
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.delete",
            {"id": 222},
        )

    def test_delete_orga_permission(self) -> None:
        self.permission_test_models["mediafile/222"]["owner_id"] = ONE_ORGANIZATION_FQID
        self.base_permission_test(
            self.permission_test_models,
            "mediafile.delete",
            {"id": 222},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
