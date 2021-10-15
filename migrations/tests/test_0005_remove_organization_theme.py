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
    write({"type": "delete", "fqid": "organization/1"})
    write({"type": "restore", "fqid": "organization/1"})

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
        {"id": 42, "f": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "organization/1",
        {"id": 42, "f": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
