from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class OrganizationTagDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models({"organization_tag/1": {"name": "test", "color": "#000000"}})

    def test_delete_correct(self) -> None:
        response = self.request("organization_tag.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("organization_tag/1")

    def test_no_permission(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request("organization_tag.delete", {"id": 1})
        self.assert_status_code(response, 403)
        self.assertEqual(
            "You are not allowed to perform action organization_tag.delete. Missing OrganizationManagementLevel: can_manage_organization",
            response.json["message"],
        )

    def test_permission(self) -> None:
        self.base_permission_test(
            {},
            "organization_tag.delete",
            {"id": 1},
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )
        self.assert_model_not_exists("organization_tag/1")

    def test_delete_utilized_organization_tag(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        self.set_models(
            {
                "meeting/1": {"organization_tag_ids": [1, 2]},
                "meeting/4": {"organization_tag_ids": [2]},
                "meeting/7": {"organization_tag_ids": [1]},
                "committee/60": {"organization_tag_ids": [1]},
                "committee/63": {"organization_tag_ids": [1]},
                "organization_tag/1": {
                    "tagged_ids": [
                        "meeting/1",
                        "meeting/7",
                        "committee/60",
                        "committee/63",
                    ]
                },
                "organization_tag/2": {
                    "name": "test2",
                    "color": "#ffffff",
                    "tagged_ids": ["meeting/1", "meeting/4"],
                },
            }
        )
        response = self.request("organization_tag.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("organization_tag/1")
        cases: dict[str, dict[str, Any]] = {
            "meeting/1": {"organization_tag_ids": [2]},
            "meeting/4": {"organization_tag_ids": [2]},
            "meeting/7": {"organization_tag_ids": None},
            "committee/60": {"organization_tag_ids": None},
            "committee/63": {"organization_tag_ids": None},
            "organization_tag/2": {"tagged_ids": ["meeting/1", "meeting/4"]},
        }
        for fqid, data in cases.items():
            self.assert_model_exists(fqid, data)
