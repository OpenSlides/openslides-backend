from tests.system.action.base import BaseActionTestCase


class RoleCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        name = "test_role"
        permissions = ["t1", "t2"]

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.create",
                    "data": [
                        {"name": name, "organisation_id": 1, "permissions": permissions}
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("role/1")
        self.assertEqual(model.get("name"), name)
        self.assertCountEqual(model["permissions"], permissions)
        self.assert_model_exists("organisation/1", {"role_ids": [1]})

    def test_create_only_required(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        name = "test_role"

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.create",
                    "data": [{"name": name, "organisation_id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("role/1")
        self.assertEqual(model.get("name"), name)

    def test_create_wrong_field(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.create",
                    "data": [
                        {
                            "name": "test_role_name",
                            "organisation_id": 1,
                            "wrong_field": "test",
                        }
                    ],
                }
            ],
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )
        self.assert_model_not_exists("role/1")

    def test_create_empty_data(self) -> None:
        response = self.client.post("/", json=[{"action": "role.create", "data": [{}]}])
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain [\\'organisation_id\\', \\'name\\'] properties",
            str(response.data),
        )
        self.assert_model_not_exists("role/1")

    def test_create_empty_data_list(self) -> None:
        response = self.client.post("/", json=[{"action": "role.create", "data": []}])
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("role/1")

    def test_not_existing_organisation(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.create",
                    "data": [{"organisation_id": 1, "name": "test_name"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model \\'organisation/1\\' does not exist.",
            str(response.data),
        )
        self.assert_model_not_exists("role/1")

    def test_wrong_field_type_permissions(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.create",
                    "data": [
                        {
                            "name": "test_role",
                            "organisation_id": 1,
                            "permissions": "Permission1",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn("data.permissions must be array", str(response.data))
        self.assert_model_not_exists("role/1")

    def test_create_prevent_duplicated_permission(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.create",
                    "data": [
                        {
                            "name": "test",
                            "organisation_id": 1,
                            "permissions": ["t1", "t1", "t3", "t4", "t3"],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("role/1")
        self.assertCountEqual(model["permissions"], ["t1", "t3", "t4"])
