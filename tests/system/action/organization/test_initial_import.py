import logging
from typing import Any

from openslides_backend.i18n.translator import Translator
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.util import INITIAL_DATA_FILE, get_initial_data_file
from tests.system.action.base import BaseActionTestCase
from tests.system.util import Profiler


class OrganizationInitialImport(BaseActionTestCase):
    def setUp(self) -> None:
        self.init_with_login = (
            False  # don't use client or write organization and first user
        )
        super().setUp()

    def test_initial_import_filled_datastore(self) -> None:
        self.create_model(
            "organization/1", {"name": "Intevation", "default_language": "en"}
        )
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn("Datastore is not empty.", response.json["message"])

    def test_initial_import_with_initial_data_file(self) -> None:
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
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
        request_data = {"data": get_initial_data_file("data/example-data.json")}
        request_data["data"]["organization"]["1"]["default_language"] = "de"
        with Profiler("data/test_initial_import_with_example_data_file.prof"):
            response = self.request(
                "organization.initial_import",
                request_data,
                anonymous=True,
                internal=True,
            )
        self.assert_status_code(response, 200)
        Translator.set_translation_language("de")
        for collection in request_data["data"]:
            if collection == "_migration_index":
                continue
            for id_ in request_data["data"][collection]:
                entry = request_data["data"][collection][id_]
                if collection == "organization":
                    for field in (
                        "login_text",
                        "legal_notice",
                        "users_email_subject",
                        "users_email_body",
                    ):
                        if entry.get(field):
                            entry[field] = Translator.translate(entry[field])
                if collection == "theme":
                    if entry.get("name"):
                        entry["name"] = Translator.translate(entry["name"])
                self.assert_model_exists(f"{collection}/{id_}", entry)

    def test_initial_import_wrong_field(self) -> None:
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["organization"]["1"]["test_field"] = "test"
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "organization/1: Invalid fields test_field (value: test)",
            response.json["message"],
        )

    def test_initial_import_missing_default_language(self) -> None:
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        del request_data["data"]["organization"]["1"]["default_language"]
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "organization/1: Missing fields default_language",
            response.json["message"],
        )

    def test_initial_import_wrong_type(self) -> None:
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["theme"]["1"]["theme_for_organization_id"] = None
        request_data["data"]["organization"]["1"]["theme_id"] = "test"
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        print(response.json)
        self.assertIn(
            "organization/1/theme_id: Type error: Type is not RelationField(to={'theme': 'theme_for_organization_id'}, is_list_field=False, on_delete=SET_NULL, required=True, constraints={}, equal_fields=[])",
            response.json["message"],
        )
        self.assertIn(
            "organization/1/theme_id: Relation Error:  points to theme/test/theme_for_organization_id, but the reverse relation for it is corrupt",
            response.json["message"],
        )

    def test_initial_import_wrong_relation(self) -> None:
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["organization"]["1"]["theme_id"] = 666
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Relation Error:  points to theme/666/theme_for_organization_id, but the reverse relation for it is corrupt",
            response.json["message"],
        )
        self.assertIn(
            "Relation Error:  points to organization/1/theme_id, but the reverse relation for it is corrupt",
            response.json["message"],
        )

    def test_inital_import_missing_required(self) -> None:
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        del request_data["data"]["organization"]["1"]["theme_id"]
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "organization/1: Missing fields theme_id", response.json["message"]
        )

    def test_initial_import_negative_default_vote_weight(self) -> None:
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["user"]["1"]["default_vote_weight"] = "-2.000000"
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "default_vote_weight must be bigger than or equal to 0.",
            response.json["message"],
        )

    def test_initial_import_empty_data(self) -> None:
        """when there is no data given, use initial_data.json for initial import"""
        request_data: dict[str, Any] = {"data": {}}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
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
        request_data = {"data": {"f": 1}}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "JSON does not match schema: data must contain ['_migration_index'] properties",
            response.json["message"],
        )

    def test_initial_import_with_MI_to_small(self) -> None:
        request_data = {"data": {"_migration_index": -1}}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "JSON does not match schema: data._migration_index must be bigger than or equal to 1",
            response.json["message"],
        )

    def test_initial_import_MI_greater_backend_MI(self) -> None:
        backend_migration_index = MigrationHelper.get_backend_migration_index()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["_migration_index"] = backend_migration_index - 1
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 200)
        self.assertIn(
            "Data imported, but must be migrated!",
            response.json["results"][0][0]["message"],
        )
        self.assertTrue(response.json["results"][0][0]["migration_needed"])

    def test_initial_import_MI_lower_backend_MI(self) -> None:
        backend_migration_index = MigrationHelper.get_backend_migration_index()
        request_data = {"data": {"_migration_index": backend_migration_index + 1}}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            " is higher than the backend ",
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

        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}

        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 200)
        self.assertIn(
            "Data imported, Migration Index set to",
            response.json["results"][0][0]["message"],
        )
        self.assertFalse(response.json["results"][0][0]["migration_needed"])

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                MigrationHelper.assert_migration_index(curs)
        manager = MigrationManager(self.env, self.services, logging)
        manager.execute_migrate_command("finalize", verbose=True)

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                MigrationHelper.assert_migration_index(curs)
