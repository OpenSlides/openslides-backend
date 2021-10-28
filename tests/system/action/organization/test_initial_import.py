from tests.system.action.base import BaseActionTestCase


class OrganizationInitialImport(BaseActionTestCase):
    def test_initial_import_filled_datastore(self) -> None:
        self.set_models({"organization/1": {}})
        request_data = {"data": self.get_initial_data()}
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        assert "Datastore is not empty." in response.json["message"]

    def test_initial_import_with_initial_data_file(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": self.get_initial_data()}
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 200)
        for collection in request_data["data"]:
            if collection == "_migration_index":
                continue
            for id_ in request_data["data"][collection]:
                self.assert_model_exists(
                    f"{collection}/{id_}", request_data["data"][collection][id_]
                )

    def test_initial_import_wrong_field(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": self.get_initial_data()}
        request_data["data"]["meeting"]["1"]["test_field"] = "test"
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "meeting/1: Invalid fields test_field (value: test)"
            in response.json["message"]
        )

    def test_initial_import_wrong_type(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": self.get_initial_data()}
        request_data["data"]["organization"]["1"]["theme_id"] = "test"
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "organization/1/theme_id: Type error: Type is not RelationField(to={Collection('theme'): 'theme_for_organization_id'}, is_list_field=False, on_delete=OnDelete.SET_NULL, required=True, constraints={}, equal_fields=[])"
            in response.json["message"]
        )

    def test_initial_import_wrong_relation(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": self.get_initial_data()}
        request_data["data"]["organization"]["1"]["theme_id"] = 666
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "Relation Error:  points to theme/666/theme_for_organization_id, but the reverse relation for it is corrupt"
            in response.json["message"]
        )
        assert (
            "Relation Error:  points to organization/1/theme_id, but the reverse relation for it is corrupt"
            in response.json["message"]
        )

    def test_inital_import_missing_required(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": self.get_initial_data()}
        del request_data["data"]["organization"]["1"]["theme_id"]
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        assert "organization/1: Missing fields theme_id" in response.json["message"]
