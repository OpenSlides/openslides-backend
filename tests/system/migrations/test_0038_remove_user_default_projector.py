def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"a": 1, "default_projector_$user_ids": [1]},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"a": 2, "default_projector_$user_ids": [2]},
        }
    )
    write({"type": "delete", "fqid": "meeting/1"})
    write({"type": "restore", "fqid": "meeting/1"})

    finalize("0038_remove_user_default_projector")

    assert_model(
        "meeting/1",
        {"a": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "meeting/1",
        {"a": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "meeting/1",
        {"a": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "meeting/1",
        {"a": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
