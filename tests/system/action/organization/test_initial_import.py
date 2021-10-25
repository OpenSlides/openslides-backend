from openslides_backend.models.base import model_registry
from tests.system.action.base import BaseActionTestCase


class OrganizationInitialImport(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        for collection in list(model_registry.keys()):
            if collection.collection.startswith(
                "fake_model"
            ) or collection.collection.startswith("dummy_model"):
                del model_registry[collection]

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
