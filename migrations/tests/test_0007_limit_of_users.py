def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": "organization/1", "fields": {"f": 1}})
    write({"type": "update", "fqid": "organization/1", "fields": {"f": 2}})
    write({"type": "delete", "fqid": "organization/1"})
    write({"type": "restore", "fqid": "organization/1"})

    finalize("0007_limit_of_users")

    assert_model(
        "organization/1",
        {"limit_of_users": 0, "f": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "organization/1",
        {"limit_of_users": 0, "f": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "organization/1",
        {"limit_of_users": 0, "f": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "organization/1",
        {"limit_of_users": 0, "f": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
