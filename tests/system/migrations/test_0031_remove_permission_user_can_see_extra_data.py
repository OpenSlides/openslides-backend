def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {"permissions": ["user.can_see_extra_data"]},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "group/1",
            "fields": {"permissions": ["user.can_see"]},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "group/1",
            "fields": {"permissions": ["user.can_see_extra_data"]},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "group/1",
            "list_fields": {
                "add": {},
                "remove": {"permissions": ["user.can_see_extra_data"]},
            },
        }
    )
    write(
        {
            "type": "update",
            "fqid": "group/1",
            "list_fields": {
                "add": {"permissions": ["user.can_see_extra_data"]},
                "remove": {},
            },
        }
    )

    finalize("0031_remove_permission_user_can_see_extra_data")

    assert_model(
        "group/1",
        {"permissions": [], "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "group/1",
        {"permissions": ["user.can_see"], "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "group/1",
        {"permissions": [], "meta_deleted": False, "meta_position": 3},
        position=3,
    )
    assert_model(
        "group/1",
        {"permissions": [], "meta_deleted": False, "meta_position": 4},
        position=4,
    )
    assert_model(
        "group/1",
        {"permissions": [], "meta_deleted": False, "meta_position": 5},
        position=5,
    )
