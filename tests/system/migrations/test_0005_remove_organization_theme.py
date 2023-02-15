ONE_ORGANIZATION_FQID = "organization/1"


def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": ONE_ORGANIZATION_FQID,
            "fields": {"id": 42, "theme": "openslides-default-theme"},
        }
    )
    write(
        {
            "type": "update",
            "fqid": ONE_ORGANIZATION_FQID,
            "fields": {"theme": "test", "f": 2},
        }
    )
    write(
        {
            "type": "update",
            "fqid": ONE_ORGANIZATION_FQID,
            "fields": {"theme": None},
        }
    )
    write({"type": "delete", "fqid": ONE_ORGANIZATION_FQID})
    write({"type": "restore", "fqid": ONE_ORGANIZATION_FQID})
    write(
        {
            "type": "create",
            "fqid": "dummy/1",
            "fields": {"f": 1},
        }
    )

    finalize("0005_remove_organization_theme")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {"id": 42, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"id": 42, "f": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"id": 42, "f": 2, "meta_deleted": False, "meta_position": 2},
        position=3,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"id": 42, "f": 2, "meta_deleted": True, "meta_position": 4},
        position=4,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"id": 42, "f": 2, "meta_deleted": False, "meta_position": 5},
        position=5,
    )
    assert_model(
        "dummy/1",
        {"f": 1, "meta_deleted": False, "meta_position": 6},
        position=6,
    )
