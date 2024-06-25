from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class CommitteeUpdateActionTest(BaseActionTestCase):
    gender_id = 5
    gender_fqid = f"gender/{gender_id}"
    gender_name = "dragon"

    def create_data(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"name": "test_organization1"},
                self.gender_fqid: {
                    "name": self.gender_name,
                    "organization_id": 1,
                },
                "gender/2": {"name": "female", "organization_id": 1},
                "user/20": {"username": "test_user20", "gender_id": self.gender_id},
                "user/21": {"username": "test_user21"},
            }
        )

    def test_update_correctly(self) -> None:
        self.create_data()
        new_name = "gender_testname_updated"
        response = self.request(
            "gender.update", {"id": self.gender_id, "name": new_name}
        )
        self.assert_status_code(response, 200)
        model = self.get_model(self.gender_fqid)
        self.assertEqual(model.get("name"), new_name)

    def test_update_empty_name(self) -> None:
        self.create_data()
        new_name = ""
        response = self.request(
            "gender.update", {"id": self.gender_id, "name": new_name}
        )
        self.assert_status_code(response, 400)
        self.assertIn("Empty gender name not allowed.", response.json["message"])
        model = self.get_model(self.gender_fqid)
        self.assertEqual(model.get("name"), self.gender_name)

    def test_update_empty(self) -> None:
        self.create_data()
        response = self.request("gender.update", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['id', 'name'] properties", response.json["message"]
        )
        model = self.get_model(self.gender_fqid)
        self.assertEqual(model.get("name"), self.gender_name)

    def test_update_empty_list(self) -> None:
        self.create_data()
        response = self.request_multi("gender.update", [])
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("gender/1")
        self.assert_model_not_exists("gender/3")
        self.assert_model_not_exists("gender/4")
        self.assert_model_not_exists("gender/6")

    def test_update_default_gender(self) -> None:
        self.create_data()
        response = self.request(
            "gender.update",
            {
                "id": 2,
                "name": "so wrong to change this gender",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot delete or update gender 'female' from default selection.",
            response.json["message"],
        )

    def test_update_wrong_id(self) -> None:
        self.create_data()
        response = self.request("gender.update", {"id": 200, "name": "xxxxx"})
        self.assert_status_code(response, 400)
        model = self.get_model(self.gender_fqid)
        self.assertEqual(model.get("name"), self.gender_name)

    def test_update_wrong_field(self) -> None:
        self.create_data()
        response = self.request("gender.update", {"id": 5, "Mercedes": "xxxxx"})
        self.assert_status_code(response, 400)
        model = self.get_model(self.gender_fqid)
        self.assertEqual(model.get("name"), self.gender_name)

    def test_update_no_permission(self) -> None:
        self.create_data()
        self.set_models(
            {"user/1": {"organization_management_level": "can_manage_users"}}
        )

        response = self.request(
            "gender.update", {"id": self.gender_id, "name": "testy"}
        )
        self.assert_status_code(response, 403)
        assert (
            "Missing OrganizationManagementLevel: can_manage_organization"
            in response.json["message"]
        )
        self.assert_model_exists(
            self.gender_fqid,
            {"id": self.gender_id, "name": self.gender_name},
        )

    def test_update_permission(self) -> None:
        self.create_data()
        self.set_models(
            {"user/1": {"organization_management_level": "can_manage_organization"}}
        )
        response = self.request(
            "gender.update", {"id": self.gender_id, "name": "testy"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            self.gender_fqid, {"id": self.gender_id, "name": "testy"}
        )
