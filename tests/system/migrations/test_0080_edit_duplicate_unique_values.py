import pytest

from typing import Any

from openslides_backend.migrations.migrations.exceptions import MigrationException

IterableData = dict[int, dict[str,Any]]
ErrorData = list[str]
# collection, setup, ids_to_delete, error
TestData = tuple[str, IterableData, list[int], list[str]|IterableData]

def do_test(write, finalize, assert_model, test_data: TestData)-> None:
    collection, setup, to_delete, expect_or_error = test_data
    write(
        *[
            {"type": "create", "fqid": f"{collection}/{id_}", "fields": data}
            for id_, data in setup.items()
        ]
    )
    if to_delete:
        write(
            *[
                {"type": "delete", "fqid": f"{collection}/{id_}"}
                for id_ in to_delete
            ]
        )
    if isinstance(expect_or_error, list):
        try:
            finalize("0080_edit_duplicate_unique_values")
            raise pytest.fail("Expected migration to fail. It didn't.")
        except MigrationException as e:
            err_str = '\n* '.join(expect_or_error)
            assert str(e) == f"Migration exception:\n* {err_str}"
    else:
        finalize("0080_edit_duplicate_unique_values")
        for id_, expect in expect_or_error.items():
            assert_model(f"{collection}/{id_}", expect)

def build_committee_test_data(fail: bool=False) -> TestData:
    setup_data: IterableData = {}
    expect_data: IterableData = {}
    setup_data[1] = expect_data[1] = {
        "name": "unproblematic",
        "external_id": "unique"
    }
    setup_data[2] = expect_data[2] = {
        "name": "foux problematic",
        "external_id": "now unique"
    }
    setup_data[3] = {
        "name": "deleted",
        "external_id": "now unique"
    }
    expect_data[3] = {
        "name": "deleted",
        "external_id": "now unique",
        "meta_deleted": True
    }
    if fail:
        setup_data[4] = {
            "name": "actual problem",
            "external_id": "not unique"
        }
        setup_data[5] = {
            "name": "actual problem's brother",
            "external_id": "not unique"
        }
        return "committee", setup_data, [3], ["committee: Ids [4, 5]: Duplicate values for {external_id} (values: {'not unique'}) cannot be handled."]
    return "committee", setup_data, [3], expect_data

def test_committee_success(write, finalize, assert_model):
    do_test(write, finalize, assert_model,build_committee_test_data())

def test_committee_error(write, finalize, assert_model):
    do_test(write, finalize, assert_model,build_committee_test_data(fail=True))
