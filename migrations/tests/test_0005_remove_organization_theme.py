def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"id": 42, "theme": "openslides-default-theme"},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"theme": "test", "f": 2},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"theme": None},
        }
    )
    write({"type": "delete", "fqid": "organization/1"})
    write({"type": "restore", "fqid": "organization/1"})
    write(
        {
            "type": "create",
            "fqid": "dummy/1",
            "fields": {"f": 1},
        }
    )

    finalize("0005_remove_organization_theme")

    assert_model(
        "organization/1",
        {"id": 42, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "organization/1",
        {"id": 42, "f": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "organization/1",
        {"id": 42, "f": 2, "meta_deleted": False, "meta_position": 3},
        position=3,
    )
    assert_model(
        "organization/1",
        {"id": 42, "f": 2, "meta_deleted": True, "meta_position": 4},
        position=4,
    )
    assert_model(
        "organization/1",
        {"id": 42, "f": 2, "meta_deleted": False, "meta_position": 5},
        position=5,
    )
    assert_model(
        "dummy/1",
        {"f": 1, "meta_deleted": False, "meta_position": 6},
        position=6,
    )
