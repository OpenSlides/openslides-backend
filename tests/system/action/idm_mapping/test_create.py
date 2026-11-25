from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class IdmMappingCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models({"idm_mapper/1": {"group_external_ids": ["AAAAAAAaaaaaaaa"]}})

    def test_create_simple(self) -> None:
        response = self.request(
            "idm_mapping.create",
            {"idm_field": "ew_its_also_a_field", "os_field": "number", "mapper_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_mapping/1",
            {"idm_field": "ew_its_also_a_field", "os_field": "number", "mapper_id": 1},
        )

    def test_create_complex(self) -> None:
        response = self.request(
            "idm_mapping.create",
            {
                "idm_field": "ew_its_also_a_field",
                "os_field": "number",
                "mapper_id": 1,
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

    def test_create_no_mapper_id(self) -> None:
        response = self.request(
            "idm_mapping.create",
            {"idm_field": "ew_its_also_a_field", "os_field": "number"},
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Action idm_mapping.create: data must contain ['mapper_id'] properties"
        )

    def test_create_as_orga_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, 1
        )
        response = self.request(
            "idm_mapping.create",
            {"idm_field": "ew_its_also_a_field", "os_field": "number", "mapper_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_mapping/1",
            {"idm_field": "ew_its_also_a_field", "os_field": "number", "mapper_id": 1},
        )

    def test_create_as_account_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, 1
        )
        response = self.request(
            "idm_mapping.create",
            {"idm_field": "ew_its_also_a_field", "os_field": "number", "mapper_id": 1},
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action idm_mapping.create. Missing OrganizationManagementLevel: can_manage_organization"
        )
