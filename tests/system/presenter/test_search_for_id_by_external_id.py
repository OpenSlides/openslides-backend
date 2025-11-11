from openslides_backend.permissions.management_levels import OrganizationManagementLevel

from .base import BasePresenterTestCase


class TestSearchForIdByExternalId(BasePresenterTestCase):
    def test_correct(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        self.create_meeting(2, meeting_data={"external_id": "234ex"})
        self.set_models(
            {
                "group/4": {"external_id": "345ex"},
                "committee/61": {"external_id": "234ex"},
            }
        )

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "meeting", "external_id": "234ex", "context_id": 61},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 2})

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "345ex", "context_id": 2},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 4})

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "committee", "external_id": "234ex", "context_id": 1},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 61})

    def test_none_found(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "group/3": {"external_id": "1ex"},
            }
        )
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "2other", "context_id": 1},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data, {"id": None, "error": "No item with '2other' was found."}
        )

    def test_many_found(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "group/2": {"external_id": "1ex"},
                "group/3": {"external_id": "1ex"},
            }
        )
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "1ex", "context_id": 1},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data, {"id": None, "error": "More then one item with '1ex' were found."}
        )

    def test_wrong_collection(self) -> None:
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "motion", "external_id": "1ex", "context_id": 1},
        )
        self.assertEqual(status_code, 400)
        self.assertEqual(
            data["message"],
            "data.collection must be one of ['committee', 'meeting', 'group']",
        )

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "user", "external_id": "123saml", "context_id": 1},
        )
        self.assertEqual(status_code, 400)
        self.assertEqual(
            data["message"],
            "data.collection must be one of ['committee', 'meeting', 'group']",
        )

    def test_no_permission(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "1ex", "context_id": 1},
        )
        self.assertEqual(status_code, 403)
        self.assertEqual(
            data["message"],
            "Missing OrganizationManagementLevel: can_manage_organization",
        )

    def test_with_locked_meeting(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        self.create_meeting(
            2, meeting_data={"external_id": "234ex", "locked_from_inside": True}
        )
        self.set_models(
            {
                "group/4": {"external_id": "345ex"},
                "committee/61": {"external_id": "234ex"},
            }
        )

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "meeting", "external_id": "234ex", "context_id": 61},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 2})

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "345ex", "context_id": 2},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": None, "error": "No item with '345ex' was found."})

        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "committee", "external_id": "234ex", "context_id": 1},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 61})

    def test_one_of_many_groups_found_due_to_meeting_lock(self) -> None:
        self.create_meeting()
        self.create_meeting(4, meeting_data={"locked_from_inside": True})
        self.set_models(
            {
                "group/3": {"external_id": "1ex"},
                "group/6": {"external_id": "1ex"},
            }
        )
        status_code, data = self.request(
            "search_for_id_by_external_id",
            {"collection": "group", "external_id": "1ex", "context_id": 1},
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"id": 3})
