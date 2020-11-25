from tests.system.action.base import BaseActionTestCase


class RoleDeleteActionTest(BaseActionTestCase):
    ROLE_ID = 1
    ROLE_FQID = "role/1"

    def create_data(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})

        self.client.post(
            "/",
            json=[
                {
                    "action": "role.create",
                    "data": [
                        {
                            "name": "role_testname",
                            "organisation_id": 1,
                            "permissions": ["t1", "t2"],
                        }
                    ],
                }
            ],
        )

    def test_delete_correct(self) -> None:
        self.create_data()
        response = self.client.post(
            "/",
            json=[{"action": "role.delete", "data": [{"id": self.ROLE_ID}]}],
        )

        self.assert_status_code(response, 200)
        self.assert_model_deleted(self.ROLE_FQID)
        self.assert_model_exists("organisation/1", {"role_ids": []})

    def test_delete_wrong_id(self) -> None:
        self.create_data()
        response = self.client.post(
            "/",
            json=[{"action": "role.delete", "data": [{"id": 2}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn("Model \\'role/2\\' does not exist.", str(response.data))
        model = self.get_model(self.ROLE_FQID)
        self.assertEqual(model.get("name"), "role_testname")
