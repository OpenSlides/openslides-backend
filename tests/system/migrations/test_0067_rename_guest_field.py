def test_migration(write, finalize, assert_model):
    write(
        {"type": "create", "fqid": "user/1", "fields": {"id": 1, "guest": True}},
        {"type": "create", "fqid": "user/2", "fields": {"id": 2, "guest": False}},
        {"type": "create", "fqid": "user/3", "fields": {"id": 3, "guest": False}},
    )
    write(
        {"type": "update", "fqid": "user/2", "fields": {"id": 2, "guest": True}},
    )
    write(
        {"type": "delete", "fqid": "user/3", "fields": {}},
    )

    finalize("0067_rename_guest_field")

    assert_model("user/1", {"id": 1, "external": True, "meta_deleted": False})
    assert_model("user/2", {"id": 2, "external": True, "meta_deleted": False})
    assert_model("user/3", {"id": 3, "external": False, "meta_deleted": True})
