def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "poll/1",
            "fields": {"a": 1, "publish_immediately": False},
        },
        {
            "type": "create",
            "fqid": "option/11",
            "fields": {"a": 1, "publish_immediately": True},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "poll/1",
            "fields": {"a": 2, "publish_immediately": True},
        },
        {
            "type": "update",
            "fqid": "option/11",
            "fields": {"a": 2, "publish_immediately": False},
        },
    )
    write({"type": "delete", "fqid": "poll/1"}, {"type": "delete", "fqid": "option/11"})
    write(
        {"type": "restore", "fqid": "poll/1"}, {"type": "restore", "fqid": "option/11"}
    )

    finalize("0027_remove_publish_immediately")

    assert_model(
        "poll/1",
        {"a": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "poll/1",
        {"a": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "poll/1",
        {"a": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "poll/1",
        {"a": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
    assert_model(
        "option/11",
        {"a": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "option/11",
        {"a": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "option/11",
        {"a": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "option/11",
        {"a": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
