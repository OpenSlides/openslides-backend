from tests.system.action.base import BaseActionTestCase


class RoleUpdateActionTest(BaseActionTestCase):
    ROLE_ID = 1
    ROLE_FQID = "role/1"
    ROLE_NAME = "role_testname"
    ROLE_PERMISSIONS = ["t1", "t2"]

    def create_data(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})

        self.client.post(
            "/",
            json=[
                {
                    "action": "role.create",
                    "data": [
                        {
                            "name": self.ROLE_NAME,
                            "organisation_id": 1,
                            "permissions": self.ROLE_PERMISSIONS,
                        }
                    ],
                }
            ],
        )

    def test_update_correct(self) -> None:
        self.create_data()
        new_name = "role_testname_updated"
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.update",
                    "data": [{"id": self.ROLE_ID, "name": new_name}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model(self.ROLE_FQID)
        self.assertEqual(model.get("name"), new_name)

    def test_update_everything_correct(self) -> None:
        self.create_data()
        new_name = "role_testname_updated"
        new_permissions = ["t3"]
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.update",
                    "data": [
                        {
                            "id": self.ROLE_ID,
                            "name": new_name,
                            "permissions": new_permissions,
                        },
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model(self.ROLE_FQID)
        self.assertEqual(model.get("name"), new_name)
        self.assertCountEqual(model["permissions"], new_permissions)

    def test_update_wrong_permissions(self) -> None:
        self.create_data()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.update",
                    "data": [
                        {"id": self.ROLE_ID, "permissions": "Permission"},
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.ROLE_FQID)
        self.assertCountEqual(model["permissions"], self.ROLE_PERMISSIONS)
        self.assertIn(
            "data[0].permissions must be array",
            str(response.data),
        )

    def test_update_wrong_superadmin_role(self) -> None:
        self.create_data()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.update",
                    "data": [
                        {
                            "id": self.ROLE_ID,
                            "superadmin_role_for_organisation_id": self.ROLE_ID,
                        },
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must not contain {\\'superadmin_role_for_organisation_id\\'} properties",
            str(response.data),
        )

    def test_update_prevent_duplicated_permission(self) -> None:
        self.create_data()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "role.update",
                    "data": [
                        {
                            "id": self.ROLE_ID,
                            "permissions": ["t1", "t1", "t3", "t4", "t3"],
                        },
                    ],
                }
            ],
        )

        self.assert_status_code(response, 200)
        model = self.get_model("role/1")
        self.assertCountEqual(model["permissions"], ["t1", "t3", "t4"])
