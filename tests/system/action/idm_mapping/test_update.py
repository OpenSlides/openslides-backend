from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class IdmMappingUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "idm_mapper/1": {"group_external_ids": ["AAAAAAAaaaaaaaa"]},
                "idm_mapping/1": {
                    "idm_field": "yo",
                    "os_field": "number",
                    "mapper_id": 1,
                },
            }
        )

    def test_update_simple(self) -> None:
        response = self.request(
            "idm_mapping.update", {"id": 1, "idm_field": "ew_its_also_a_field"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_mapping/1",
            {"idm_field": "ew_its_also_a_field", "os_field": "number", "mapper_id": 1},
        )

    def test_update_complex(self) -> None:
        response = self.request(
            "idm_mapping.update",
            {
                "id": 1,
                "idm_field": "ew_its_also_a_field",
                "default_value": "I'ma default",
                "allow_update": True,
                "override_default": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_mapping/1",
            {
                "idm_field": "ew_its_also_a_field",
                "os_field": "number",
                "mapper_id": 1,
                "default_value": "I'ma default",
                "allow_update": True,
                "override_default": True,
            },
        )

    def test_update_as_orga_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, 1
        )
        response = self.request(
            "idm_mapping.update", {"id": 1, "idm_field": "ew_its_also_a_field"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_mapping/1",
            {"idm_field": "ew_its_also_a_field", "os_field": "number", "mapper_id": 1},
        )

    def test_update_as_account_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, 1
        )
        response = self.request(
            "idm_mapping.update", {"id": 1, "idm_field": "ew_its_also_a_field"}
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action idm_mapping.update. Missing OrganizationManagementLevel: can_manage_organization"
        )
