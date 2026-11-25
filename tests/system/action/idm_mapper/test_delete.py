from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class IdmMapperDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models({"idm_mapper/1": {"group_external_ids": ["AAAAAAAaaaaaaaa"]}})

    def test_delete(self) -> None:
        response = self.request("idm_mapper.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("idm_mapper/1")

    def test_delete_with_submodels(self) -> None:
        self.set_models(
            {
                "idm_condition/1": {
                    "idm_field": "ew_its_a_field",
                    "regex": "[a]*",
                    "mapper_id": 1,
                },
                "idm_mapping/1": {
                    "idm_field": "ew_its_also_a_field",
                    "os_field": "number",
                    "mapper_id": 1,
                },
            }
        )
        response = self.request("idm_mapper.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("idm_mapper/1")
        self.assert_model_not_exists("idm_condition/1")
        self.assert_model_not_exists("idm_mapping/1")

    def test_delete_as_orga_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, 1
        )
        response = self.request("idm_mapper.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("idm_mapper/1")

    def test_delete_as_account_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, 1
        )
        response = self.request("idm_mapper.delete", {"id": 1})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action idm_mapper.delete. Missing OrganizationManagementLevel: can_manage_organization"
        )
        self.assert_model_exists("idm_mapper/1")
