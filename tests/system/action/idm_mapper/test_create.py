from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class IdmMapperCreateActionTest(BaseActionTestCase):
    def test_create_simple(self) -> None:
        response = self.request(
            "idm_mapper.create",
            {"group_external_ids": ["sugar", "spice", "everything_nice"]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "idm_mapper/1",
            {
                "group_external_ids": ["sugar", "spice", "everything_nice"],
                "organization_id": 1,
            },
        )

    def test_create_external_ids_empty(self) -> None:
        response = self.request("idm_mapper.create", {"group_external_ids": []})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Creation of idm_mapper/1: You try to set following required fields to an empty value: ['group_external_ids']"
        )

    def test_create_with_weight(self) -> None:
        response = self.request(
            "idm_mapper.create",
            {"group_external_ids": ["bling", "bang", "born"], "weight": 5},
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Action idm_mapper.create: data must not contain {'weight'} properties"
        )

    def test_create_no_external_ids(self) -> None:
        response = self.request("idm_mapper.create", {"weight": 5})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Action idm_mapper.create: data must contain ['group_external_ids'] properties"
        )

    def test_create_as_orga_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, 1
        )
        response = self.request("idm_mapper.create", {"group_external_ids": [":)"]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("idm_mapper/1", {"group_external_ids": [":)"]})

    def test_create_as_account_admin(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, 1
        )
        response = self.request("idm_mapper.create", {"group_external_ids": [":)"]})
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action idm_mapper.create. Missing OrganizationManagementLevel: can_manage_organization"
        )
