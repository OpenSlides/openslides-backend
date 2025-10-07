from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from openslides_backend.i18n.translator import Translator
from openslides_backend.migrations import (
    assert_migration_index,
    get_backend_migration_index,
)
from openslides_backend.migrations.migrate import MigrationWrapper
from openslides_backend.models import fields
from openslides_backend.models.base import model_registry
from openslides_backend.shared.util import (
    EXAMPLE_DATA_FILE,
    INITIAL_DATA_FILE,
    ONE_ORGANIZATION_FQID,
    get_initial_data_file,
)
from tests.system.action.base import BaseActionTestCase
from tests.system.util import Profiler, performance


class OrganizationInitialImport(BaseActionTestCase):
    def setUp(self) -> None:
        self.init_with_login = (
            False  # don't use client or write organization and first user
        )
        super().setUp()

    def get_formatted_value(
        self,
        field_name: str,
        value: Any,
        collection: str,
        should_be_translated: bool,
    ) -> Any:
        # TODO: remove when empty back relations are removed from initial data files
        if value == [] and not (
            collection == "motion_state" and field_name == "restrictions"
        ):
            return None

        # Update translatable values
        translatable_fields = {
            "organization": [
                "login_text",
                "legal_notice",
                "users_email_subject",
                "users_email_body",
            ],
            "theme": ["name"],
        }
        if should_be_translated and field_name in translatable_fields.get(
            collection, []
        ):
            return Translator.translate(value)

        # Update value types
        field = model_registry[collection].try_get_field(field_name)
        match type(field):
            case fields.DecimalField:
                return Decimal(value)
            # TODO: add timestamp field to EXAMPLE_DATA_FILE
            case fields.TimestampField:
                return datetime.fromtimestamp(value, ZoneInfo("UTC"))
            case _:
                return value

    def validate_imported_data(self, imported_data: dict[str, Any]) -> None:
        lang = imported_data["organization"]["1"]["default_language"]
        should_be_translated = lang != "en"
        if should_be_translated:
            Translator.set_translation_language(lang)

        for collection, instances in imported_data.items():
            if collection == "_migration_index":
                continue
            for id_, data in instances.items():
                expected_data = {
                    field_name: self.get_formatted_value(
                        field_name, value, collection, should_be_translated
                    )
                    for field_name, value in data.items()
                }
                self.assert_model_exists(f"{collection}/{id_}", expected_data)

    def test_initial_import_filled_datastore(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "name": "Intevation",
                    "default_language": "en",
                    "theme_id": 1,
                },
                "theme/1": {"name": "Intevation theme"},
            }
        )
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn("Datastore is not empty.", response.json["message"])

    def test_initial_import_with_initial_data_file(self) -> None:
        initial_data = get_initial_data_file(INITIAL_DATA_FILE)
        request_data = {"data": initial_data}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 200)
        self.validate_imported_data(initial_data)

    def test_initial_import_empty_data(self) -> None:
        """when there is no data given, use initial_data.json for initial import"""
        response = self.request(
            "organization.initial_import", {"data": {}}, anonymous=True, internal=True
        )
        self.assert_status_code(response, 200)
        self.validate_imported_data(get_initial_data_file(INITIAL_DATA_FILE))

    @performance
    def test_initial_import_with_example_data_file(self) -> None:
        self.datastore.truncate_db()
        request_data = {"data": get_initial_data_file(EXAMPLE_DATA_FILE)}
        request_data["data"]["organization"]["1"]["default_language"] = "de"
        with Profiler("data/test_initial_import_with_example_data_file.prof"):
            response = self.request(
                "organization.initial_import",
                request_data,
                anonymous=True,
                internal=True,
            )
        self.assert_status_code(response, 200)
        self.validate_imported_data(request_data["data"])

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

    def test_initial_import_without_MI(self) -> None:
        request_data = {"data": {"gender": {"1": {"id": 1, "name": "male"}}}}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "JSON does not match schema: data must contain ['_migration_index'] properties",
            response.json["message"],
        )

    def test_initial_import_with_MI_too_small(self) -> None:
        request_data = {"data": {"_migration_index": -1}}
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "JSON does not match schema: data._migration_index must be bigger than or equal to 1",
            response.json["message"],
        )

    @pytest.mark.skip("TODO: unskip once migration_index usage is fixed.")
    def test_initial_import_MI_greater_backend_MI(self) -> None:
        backend_migration_index = get_backend_migration_index()
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

    @pytest.mark.skip("TODO: unskip once migration_index usage is fixed.")
    def test_initial_import_MI_lower_backend_MI(self) -> None:
        backend_migration_index = get_backend_migration_index()
        request_data = {"data": get_initial_data_file(INITIAL_DATA_FILE)}
        request_data["data"]["_migration_index"] = backend_migration_index + 1
        response = self.request(
            "organization.initial_import", request_data, anonymous=True, internal=True
        )
        self.assert_status_code(response, 400)
        self.assertIn(" is higher than the backend ", response.json["message"])

    # TODO: check again once migration_index usage is fixed
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
        assert_migration_index()

        handler = MigrationWrapper(verbose=True)
        handler.execute_command("finalize")
        assert_migration_index()
