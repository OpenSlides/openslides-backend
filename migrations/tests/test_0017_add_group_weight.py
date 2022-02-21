def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": "group/1", "fields": {"id": 42}})
    write({"type": "update", "fqid": "group/1", "fields": {"f": 2}})
    write({"type": "delete", "fqid": "group/1"})
    write({"type": "restore", "fqid": "group/1"})

    finalize("0017_add_group_weight")

    assert_model(
        "group/1",
        {"id": 42, "weight": 42, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "group/1",
        {"id": 42, "weight": 42, "f": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "group/1",
        {"id": 42, "weight": 42, "f": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "group/1",
        {"id": 42, "weight": 42, "f": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
