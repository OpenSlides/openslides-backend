from typing import Any, Dict

from migrations import assert_migration_index, get_backend_migration_index
from migrations.migrate import MigrationWrapper
from openslides_backend.shared.util import INITIAL_DATA_FILE, get_initial_data_file
from tests.system.action.base import BaseActionTestCase


class OrganizationInitialImport(BaseActionTestCase):
    def test_initial_import_filled_datastore(self) -> None:
        self.set_models({"organization/1": {}})
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        assert "Datastore is not empty." in response.json["message"]

    def test_initial_import_with_initial_data_file(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 200)
        for collection in request_data["data"]:
            if collection == "_migration_index":
                continue
            for id_ in request_data["data"][collection]:
                self.assert_model_exists(
                    f"{collection}/{id_}", request_data["data"][collection][id_]
                )

    def test_initial_import_with_example_data_file(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": get_initial_data_file("global/data/example-data.json")}
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
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["organization"]["1"]["test_field"] = "test"
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        assert (
            "organization/1: Invalid fields test_field (value: test)"
            in response.json["message"]
        )

    def test_initial_import_wrong_type(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["theme"]["1"]["theme_for_organization_id"] = None
        request_data["data"]["organization"]["1"]["theme_id"] = "test"
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        print(response.json)
        assert (
            "organization/1/theme_id: Type error: Type is not RelationField(to={Collection('theme'): 'theme_for_organization_id'}, is_list_field=False, on_delete=OnDelete.SET_NULL, required=True, constraints={}, equal_fields=[])"
            in response.json["message"]
        )

    def test_initial_import_wrong_relation(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
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
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        del request_data["data"]["organization"]["1"]["theme_id"]
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        assert "organization/1: Missing fields theme_id" in response.json["message"]

    def test_initial_import_negative_default_vote_weight(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["user"]["1"]["default_vote_weight"] = "-2.000000"
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "default_vote_weight must be bigger than or equal to 0.",
            response.json["message"],
        )

    def test_initial_import_negative_vote_weight(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["user"]["1"]["vote_weight_$"] = ["1"]
        request_data["data"]["user"]["1"]["vote_weight_$1"] = "-2.000000"
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "vote_weight_$ must be bigger than or equal to 0.", response.json["message"]
        )

    def test_initial_import_negative_vote_weight_fields(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["user"]["1"]["default_vote_weight"] = "-2.000000"
        request_data["data"]["user"]["1"]["vote_weight_$"] = ["1"]
        request_data["data"]["user"]["1"]["vote_weight_$1"] = "-2.000000"
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "default_vote_weight must be bigger than or equal to 0.",
            response.json["message"],
        )
        self.assertIn(
            "vote_weight_$ must be bigger than or equal to 0.", response.json["message"]
        )

    def test_initial_import_empty_data(self) -> None:
        """when there is no data given, use initial_data.json for initial import"""
        self.datastore.truncate_db()
        request_data: Dict[str, Any] = {"data": {}}
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 200)
        initial_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        for collection in initial_data["data"]:
            if collection == "_migration_index":
                continue
            for id_ in initial_data["data"][collection]:
                self.assert_model_exists(
                    f"{collection}/{id_}", initial_data["data"][collection][id_]
                )

    def test_initial_import_without_MI(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": {"1": 1}}
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "Data must have a valid migration index in `_migration_index`.",
            response.json["message"],
        )

    def test_initial_import_with_MI_to_small(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": {"_migration_index": -1}}
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "Data must have a valid migration index >= 1, but has",
            response.json["message"],
        )

    def test_initial_import_MI_greater_backend_MI(self) -> None:
        self.datastore.truncate_db()
        backend_migration_index = get_backend_migration_index()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["_migration_index"] = backend_migration_index - 1
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 200)
        self.assertIn(
            "Data imported, but must be migrated!",
            response.json["results"][0][0]["message"],
        )
        self.assertTrue(response.json["results"][0][0]["migration_needed"])

    def test_initial_import_MI_lower_backend_MI(self) -> None:
        self.datastore.truncate_db()
        backend_migration_index = get_backend_migration_index()
        request_data = {"data": {"_migration_index": backend_migration_index + 1}}
        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 400)
        self.assertIn(
            "Migration indices do not match: Data has",
            response.json["message"],
        )

    def test_play_with_migrations(self) -> None:
        """
        - Loads the initial_data.json into memory
        - asserts that the MI from initial_json.data is equal to backends migration files MI
        - with request the data is loaded into database without any migration
        - calls the finalizing migrations of database, which sets the database to the MI of backend MI
        - asserts that the MIs from backend and database are equal
        """

        self.datastore.truncate_db()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        data_migration_index = request_data["data"]["_migration_index"]
        backend_migration_index = get_backend_migration_index()
        assert data_migration_index == backend_migration_index

        response = self.request("organization.initial_import", request_data)
        self.assert_status_code(response, 200)
        self.assertIn(
            "Data imported, Migration Index set to",
            response.json["results"][0][0]["message"],
        )
        self.assertFalse(response.json["results"][0][0]["migration_needed"])
        assert_migration_index()

        handler = MigrationWrapper(verbose=True)
        handler.execute_command("finalize")
        assert_migration_index()
