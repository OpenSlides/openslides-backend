def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {"id": 1, "permissions": ["motion.can_manage"]},
        },
        {
            "type": "create",
            "fqid": "group/2",
            "fields": {
                "id": 2,
                "permissions": ["motion.can_manage", "assignment.can_manage"],
            },
        },
        {
            "type": "create",
            "fqid": "group/3",
            "fields": {"id": 3, "permissions": ["assignment.can_manage"]},
        },
        {
            "type": "create",
            "fqid": "group/4",
            "fields": {"id": 4, "permissions": ["motion.can_manage_polls"]},
        },
        {
            "type": "create",
            "fqid": "group/5",
            "fields": {
                "id": 5,
                "permissions": [
                    "motion.can_manage",
                    "motion.can_manage_polls",
                    "user.can_see",
                ],
            },
        },
        {"type": "create", "fqid": "group/6", "fields": {"id": 6, "permissions": []}},
        {
            "type": "create",
            "fqid": "group/7",
            "fields": {
                "id": 7,
                "permissions": ["motion.can_manage", "assignment.can_manage"],
            },
        },
        {
            "type": "create",
            "fqid": "group/8",
            "fields": {"id": 8, "permissions": ["motion.can_manage"]},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "group/8",
            "fields": {"permissions": ["assignment.can_manage", "user.can_manage"]},
        },
    )
    write(
        {"type": "delete", "fqid": "group/7", "fields": {}},
    )

    finalize("0068_split_off_poll_permissions")

    assert_model(
        "group/1",
        {
            "id": 1,
            "permissions": ["motion.can_manage", "motion.can_manage_polls"],
            "meta_deleted": False,
        },
    )
    assert_model(
        "group/2",
        {
            "id": 2,
            "permissions": [
                "motion.can_manage",
                "assignment.can_manage",
                "motion.can_manage_polls",
                "assignment.can_manage_polls",
            ],
            "meta_deleted": False,
        },
    )
    assert_model(
        "group/3",
        {
            "id": 3,
            "permissions": ["assignment.can_manage", "assignment.can_manage_polls"],
            "meta_deleted": False,
        },
    )
    assert_model(
        "group/4",
        {"id": 4, "permissions": ["motion.can_manage_polls"], "meta_deleted": False},
    )
    assert_model(
        "group/5",
        {
            "id": 5,
            "permissions": [
                "motion.can_manage",
                "motion.can_manage_polls",
                "user.can_see",
            ],
            "meta_deleted": False,
        },
    )
    assert_model("group/6", {"id": 6, "permissions": [], "meta_deleted": False})
    assert_model(
        "group/7",
        {
            "id": 7,
            "permissions": ["motion.can_manage", "assignment.can_manage"],
            "meta_deleted": True,
        },
    )
    assert_model(
        "group/8",
        {
            "id": 8,
            "permissions": [
                "assignment.can_manage",
                "user.can_manage",
                "assignment.can_manage_polls",
            ],
            "meta_deleted": False,
        },
    )
