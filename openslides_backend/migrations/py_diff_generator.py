import os
import subprocess
from string import Template

from meta.dev.src.generate_sql_schema import Helper
from meta.dev.src.helper_get_names import HelperGetNames
from meta.dev.src.typing import PG_TYPES
from openslides_backend.migrations.migration_helper import (
    MIGRATIONS_PATH,
    MigrationHelper,
)
from openslides_backend.migrations.yaml_diff_generator import (
    PREV_MODELS,
    FieldAttributes,
)
from openslides_backend.shared.patterns import Collection, Field


class DiffMixinHelper:
    @staticmethod
    def get_typed_migration_tables(
        migration_tables: dict[Collection, list[Field]],
    ) -> dict[Collection, tuple[list[Field], dict[Field, str]]]:
        """
        For each collection in migration_tables transforms list of fields into
        a tuple with 2 elements:
        [0] - list of fields without dependencies -> can be copied into the
              migration table as is
        [1] - dictionary of fields and their new types -> for saving data
              from fields with dependencies (intermediate tables or enum types):
              - relation               ->  number
              - relation-list          ->  number[]
              - generic-relation       ->  string
              - generic-relation-list  ->  string[]
              - enum                   ->  string
              - enum[]                 ->  string[]
        """
        typed_migration_tables = {}
        for collection, fields in migration_tables.items():
            unchanged_fields: list[Field] = []
            changed_fields: dict[Field, str] = {}
            for field in fields:
                fdata = PREV_MODELS[collection]["fields"][field]
                normalized_type = None
                if fdata.get("to"):
                    normalized_type = (
                        "string" if "generic" in fdata["type"] else "number"
                    )
                    if "list" in fdata["type"]:
                        normalized_type += "[]"
                elif any(fdata.get(attr) for attr in FieldAttributes.enum_definitions):
                    normalized_type = fdata["type"]

                if normalized_type:
                    if isinstance((pg_type := PG_TYPES[normalized_type]), Template):
                        pg_type = pg_type.substitute(
                            {
                                "maxLength": Helper.get_varchar_max_length(fdata),
                            }
                        )
                    changed_fields[field] = pg_type
                else:
                    unchanged_fields.append(field)
            typed_migration_tables[collection] = (unchanged_fields, changed_fields)
        return typed_migration_tables

    @classmethod
    def generate_diff_mixin(cls) -> None:
        """
        If migration_tables are defined in the migration class, builds
        typed_migration_tables for using in data_preparation method and writes them
        into DiffMixin class in the file next to the migration class.
        """
        mig_directory = MigrationHelper.get_last_migration_directory()
        migration_tables = getattr(
            MigrationHelper.get_migration_class(mig_directory), "migration_tables", None
        )
        if not migration_tables:
            print(
                "No migration_tables defined in the migration class -> Skipping DiffMixin generation"
            )
            return

        diff_mixin_path = os.path.join(MIGRATIONS_PATH, mig_directory, "diff_mixin.py")
        with open(diff_mixin_path, "w") as f:
            f.write(
                "# Code generated. DO NOT EDIT.\n"
                "# Import DiffMixin to the migration file and extend it in the Migration class.\n"
                "\n\n"
                "class DiffMixin:\n"
                f"\ttyped_migration_tables = {cls.get_typed_migration_tables(migration_tables)}"
            )
            print(f"{diff_mixin_path} successfully created.")
        subprocess.call(f"black {diff_mixin_path}", shell=True)
        cls.generate_diff_mixin_debug()

    @classmethod
    def generate_diff_mixin_debug(cls) -> None:
        lines = ""
        mig_directory = MigrationHelper.get_last_migration_directory()
        migration_tables = getattr(
            MigrationHelper.get_migration_class(mig_directory), "migration_tables", None
        )
        assert migration_tables is not None

        for collection, fields_data in cls.get_typed_migration_tables(
            migration_tables
        ).items():
            query_fields = [
                *[field_name for field_name in fields_data[0]],
                *[
                    f"{field_name}::{simple_type} AS {field_name}"
                    for field_name, simple_type in fields_data[1].items()
                ],
            ]

            target_table = HelperGetNames.get_table_name(collection, migration=True)
            lines += f"CREATE TABLE {target_table} AS SELECT {', '.join(query_fields)} FROM \"{collection}\";\n"

        with open(
            os.path.join(
                MIGRATIONS_PATH,
                mig_directory,
                "diff_mixin_debug.sql",
            ),
            "w",
        ) as f:
            f.write(lines)
