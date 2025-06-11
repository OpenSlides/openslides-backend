from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class GenderDeleteActionTest(BaseActionTestCase):
    gender_id = 5
    gender_fqid = f"gender/{gender_id}"
    gender_name = "fairy"

    def create_data(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"gender_ids": [self.gender_id]},
                "user/20": {"gender_id": 1},
                "user/21": {"gender_id": self.gender_id},
                "gender/1": {
                    "id": 1,
                    "name": "male",
                    "organization_id": 1,
                    "user_ids": [20],
                },
                self.gender_fqid: {
                    "id": self.gender_id,
                    "name": self.gender_name,
                    "organization_id": 1,
                    "user_ids": [21],
                },
            }
        )

    def test_delete_correctly(self) -> None:
        self.create_data()
        self.set_models(
            {
                "gender/6": {
                    "name": "dragon",
                    "organization_id": 1,
                },
                ONE_ORGANIZATION_FQID: {"gender_ids": [1, self.gender_id, 6]},
            }
        )
        response = self.request("gender.delete", {"id": self.gender_id})

        self.assert_status_code(response, 200)
        self.assert_model_not_exists(self.gender_fqid)

        self.assert_model_exists("user/20", {"gender_id": 1})
        self.assert_model_exists("user/21", {"gender_id": None})
        organization1 = self.get_model(ONE_ORGANIZATION_FQID)
        self.assertCountEqual(organization1["gender_ids"], [1, 6])
        self.assert_model_exists("gender/1", {"name": "male"})
        self.assert_model_exists("gender/6", {"name": "dragon"})

    def test_delete_wrong_id(self) -> None:
        self.create_data()
        response = self.request("gender.delete", {"id": 6})
        self.assert_status_code(response, 400)
        self.assertIn("Model 'gender/6' does not exist.", response.json["message"])
        self.assert_model_exists(self.gender_fqid)

    def test_delete_default_gender(self) -> None:
        self.create_data()

        response = self.request("gender.delete", {"id": 1})

        self.assert_status_code(response, 400)
        assert (
            "Cannot delete or update gender 'male' from default selection."
            in response.json["message"]
        )
        self.assert_model_exists("gender/1", {"name": "male"})

    def test_delete_no_permission(self) -> None:
        self.create_data()
        self.set_models({"user/1": {"organization_management_level": None}})

        response = self.request("gender.delete", {"id": self.gender_id})
        self.assert_status_code(response, 403)
        assert (
            "Missing OrganizationManagementLevel: can_manage_users"
            in response.json["message"]
        )
        self.assert_model_exists(self.gender_fqid)

    def test_delete_permission(self) -> None:
        self.create_data()
        self.set_models(
            {"user/1": {"organization_management_level": "can_manage_users"}}
        )

        response = self.request("gender.delete", {"id": self.gender_id})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists(self.gender_fqid)
