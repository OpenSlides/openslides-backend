import pytest

from openslides_backend.datastore.reader.core.requests import GetManyRequestPart
from openslides_backend.datastore.shared.util.exceptions import ModelDoesNotExist
from openslides_backend.migrations.core.migration_reader import (
    MigrationReader,
    MigrationReaderImplementationMemory,
)
from openslides_backend.shared.filters import FilterOperator

model = {"id": 1, "f": 1, "g": "test", "sub_dict": {"sub_list": []}}


def check_migration_reader(migration_reader: MigrationReader):
    mapped_fields = list(model.keys())
    assert migration_reader.get("a/1", mapped_fields) == model
    with pytest.raises(ModelDoesNotExist):
        migration_reader.get("a/2")
    assert migration_reader.get_many(
        [GetManyRequestPart("a", [1, 2], mapped_fields)]
    ) == {"a": {1: model}}
    assert migration_reader.get_all("a", mapped_fields) == {1: model}
    assert migration_reader.filter("a", FilterOperator("f", "=", 1), mapped_fields) == {
        1: model
    }
    assert migration_reader.exists("a", FilterOperator("f", "<", 2)) is True
    assert migration_reader.count("a", FilterOperator("g", "~=", "TEST")) == 1
    assert migration_reader.min("a", FilterOperator("f2", "=", None), "f") == 1
    assert migration_reader.max("a", FilterOperator("g", "=", "other"), "f") is None
    assert migration_reader.is_alive("a/1") is True
    assert migration_reader.is_deleted("a/1") is False
    assert migration_reader.model_exists("a/1") is True


def test_migration_reader(write, migration_reader: MigrationReader, connection_handler):
    write({"type": "create", "fqid": "a/1", "fields": model})

    with connection_handler.get_connection_context():
        check_migration_reader(migration_reader)


def test_migration_reader_memory():
    migration_reader = MigrationReaderImplementationMemory()
    migration_reader.models = {"a/1": model}
    check_migration_reader(migration_reader)
