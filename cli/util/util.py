import os
import subprocess
from argparse import ArgumentParser, Namespace
from io import StringIO, TextIOBase
from typing import Any, cast

import requests
import yaml

from meta.dev.src.generate_sql_schema import Helper
from meta.dev.src.helper_get_names import DEFAULT_COLLECTIONS_DIR as SOURCE_COLLECTIONS
from meta.dev.src.helper_get_names import (
    FieldSqlErrorType,
    HelperGetNames,
    InternalHelper,
    TableFieldType,
)

ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
)


def parse_arguments(default: str) -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("filename", nargs="?", default=default)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def open_yml_file(file: str) -> Any:
    print(os.path.abspath(file))
    if os.path.isfile(file):
        with open(file, "rb") as x:
            models_yml = x.read()
    else:
        models_yml = requests.get(file).content
    return yaml.safe_load(models_yml)


def get_collection_names_and_filenames() -> dict[str, str]:
    filenames = sorted(os.listdir(SOURCE_COLLECTIONS))
    return {os.path.splitext(filename)[0]: filename for filename in filenames}


def load_fields(filename: str) -> dict[str, Any]:
    path = f"{SOURCE_COLLECTIONS}/{filename}"
    content = get_file_content_text(path)
    return yaml.safe_load(content)


def get_file_content_text(file: str) -> str:
    if os.path.isfile(file):
        with open(file) as x:
            return x.read()
    else:
        raise Exception(f"{file} is not a file.")


def open_output(destination: str, check: bool) -> TextIOBase:
    if check:
        return StringIO()
    else:
        return open(destination, "w")


def assert_equal(stream: TextIOBase, destination: str) -> None:
    result = subprocess.run(
        ["black", "-c", cast(StringIO, stream).getvalue()],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    result.check_returncode()
    with open(destination) as f:
        assert f.read() == result.stdout


def get_view_field_state_write_fields(
    collection_name: str, field_name: str, field_def: dict[str, Any]
) -> tuple[bool, bool, tuple[str, str, str, list[str]] | None]:
    """
    Purpose:
        Checks whether a field is a view field and if other fields need to be written in an intermediate
        table.
    Input:
    - collection_name
    - field_name
    - field_def : represents the definition of the field ( field_name in collection_name )
    Returns:
    - is_view_field : whether the field is a view field or not
    - is_primary: wether the field is primary or not
    - write_fields:
        - None if no fields need to be written
        - Tuple
            table_name : name of the intermediate table
            field1
            field2
            foreign_fields
    """
    # variable declaration
    own: TableFieldType
    field_type: str
    state: FieldSqlErrorType
    primary: bool
    error: str
    is_view_field: bool
    foreign: TableFieldType
    foreign_type: str
    write_fields: tuple[str, str, str, list[str]] | None = None

    own = TableFieldType(collection_name, field_name, field_def)
    field_type = field_def.get("type", "")

    # get the foreign field list and check the relations
    foreign_fields = InternalHelper.get_definitions_from_foreign_list(
        field_def.get("to", None), field_def.get("reference", None)
    )
    state, primary, _, error = InternalHelper.check_relation_definitions(
        own, foreign_fields
    )
    is_view_field = state == FieldSqlErrorType.SQL

    if not field_def.get("sql"):
        foreign = foreign_fields[0]
        foreign_type = foreign.field_def.get("type", "")
        if "relation-list" == field_type == foreign_type:
            write_fields = Helper.get_nm_table_name_and_fields(own, foreign) + ([],)
        elif "generic-relation-list" in (field_type, foreign_type):
            write_fields = get_write_fields_for_generic(own, foreign_fields, primary)

    assert error == "", error

    return is_view_field, primary, write_fields


def get_write_fields_for_generic(
    own: TableFieldType, foreign_fields: list[TableFieldType], primary: bool
) -> tuple[str, str, str, list[str]] | None:
    if primary:
        table_name = HelperGetNames.get_gm_table_name(own)
    else:
        table_name = HelperGetNames.get_gm_table_name(foreign_fields[0])
    field1 = f"{own.table}_{own.ref_column}"
    field2 = own.intermediate_column
    return (
        table_name,
        field1,
        field2,
        [f"{field2}_{field.table}_{field.ref_column}" for field in foreign_fields],
    )
