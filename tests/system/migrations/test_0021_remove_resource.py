from tests.system.migrations.conftest import DoesNotExist

ONE_ORGANIZATION_FQID = "organization/1"


def test_migration(write, finalize, assert_model, read_model):
    write(
        {
            "type": "create",
            "fqid": ONE_ORGANIZATION_FQID,
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
            "fqid": ONE_ORGANIZATION_FQID,
            "fields": {"resource_ids": None},
        },
    )

    finalize("0021_remove_resource")

    # resource is never created
    assert_model("resource/8", DoesNotExist(), position=2)

    assert_model(
        ONE_ORGANIZATION_FQID,
        {"id": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "theme/11",
        {"id": 11, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"id": 1, "meta_deleted": False, "meta_position": 1},
        position=3,
    )
