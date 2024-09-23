def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {"id": 1, "is_active": True},
        },
        {
            "type": "create",
            "fqid": "user/2",
            "fields": {"id": 2, "is_active": False},
        },
        {
            "type": "create",
            "fqid": "user/3",
            "fields": {"id": 3},
        },
        {
            "type": "create",
            "fqid": "user/4",
            "fields": {"id": 4, "is_active": None},
        },
        {
            "type": "create",
            "fqid": "user/5",
            "fields": {"id": 5},
        },
    )
    write({"type": "delete", "fqid": "user/5", "fields": {}})

    finalize("0055_is_active_true_default")

    for i in [1, 3, 4]:
        assert_model(
            f"user/{i}",
            {"id": i, "is_active": True},
        )
    assert_model(
        "user/2",
        {"id": 2, "is_active": False},
    )
