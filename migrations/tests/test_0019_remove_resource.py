import pytest
from datastore.shared.util.exceptions import ModelDoesNotExist


def test_migration(write, finalize, assert_model, read_model):
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"id": 1, "resource_ids": [8]},
        },
        {
            "type": "create",
            "fqid": "resource/8",
            "fields": {"id": 8, "token": "weblogo"},
        },
        {
            "type": "create",
            "fqid": "theme/11",
            "fields": {"id": 11},
        },
    )

    write(
        {
            "type": "update",
            "fqid": "resource/8",
            "fields": {"token": "testlogo"},
        }
    )
    write(
        {
            "type": "delete",
            "fqid": "resource/8",
            "fields": {"token": "testlogo"},
        },
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"resource_ids": None},
        },
    )

    finalize("0019_remove_resource")
    assert_model(
        "organization/1",
        {"id": 1, "meta_deleted": False, "meta_position": 3},
        position=3,
    )
    with pytest.raises(ModelDoesNotExist):
        read_model("resource/8", position=3)
