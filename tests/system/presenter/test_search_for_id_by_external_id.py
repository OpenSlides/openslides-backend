from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestSearchForIdByExternalId(BasePresenterTestCase):
    def test_correct(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                },
                "user/7": {"saml_id": "123saml", "username": "test"},
                "meeting/2": {"name": "test meeting", "external_id": "234ex"},
                "group/8": {"name": "test group", "external_id": "345ex"},
                "committee/11": {"name": "test committee", "external_id": "234ex"},
            }
        )
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "user", "external_id": "123saml"},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 7})

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "meeting", "external_id": "234ex"},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 2})

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "345ex"},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 8})

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "committee", "external_id": "234ex"},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 11})

    def test_none_found(self) -> None:
        self.set_models({"group/8": {"name": "test group", "external_id": "1ex"}})
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "2other"},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data, {"id": None, "error": "No item with '2other' was found."}
        )

    def test_many_found(self) -> None:
        self.set_models(
            {
                "group/8": {"name": "test group", "external_id": "1ex"},
                "group/9": {"name": "test group 2", "external_id": "1ex"},
            }
        )
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "1ex"},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data, {"id": None, "error": "More then one item with '1ex' were found."}
        )

    def test_wrong_collection(self) -> None:
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "motion", "external_id": "1ex"},
        )
        self.assertEqual(status_code, 400)
        self.assertEqual(
            data["message"],
            "data.collection must be one of ['user', 'committee', 'meeting', 'group']",
        )

    def test_no_permission(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                }
            }
        )
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "1ex"},
        )
        self.assertEqual(status_code, 403)
        self.assertEqual(
            data["message"],
            "Missing OrganizationManagementLevel: can_manage_organization",
        )
