def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "id": 1,
                "group_ids": [1],
                "meeting_user_ids": [101, 201],
            },
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {
                "id": 2,
                "group_ids": [2],
                "meeting_user_ids": [102, 202],
            },
        },
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "id": 1,
                "meeting_id": 1,
                "meeting_user_ids": [101],
            },
        },
        {
            "type": "create",
            "fqid": "group/2",
            "fields": {
                "id": 2,
                "meeting_id": 2,
                "meeting_user_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "user/10",
            "fields": {
                "id": 10,
                "meeting_user_ids": [101, 102],
            },
        },
        {
            "type": "create",
            "fqid": "user/20",
            "fields": {
                "id": 20,
                "meeting_user_ids": [201, 202],
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/101",
            "fields": {
                "id": 102,
                "meeting_id": 1,
                "group_ids": [1],
                "user_id": 10,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/102",
            "fields": {
                "id": 102,
                "meeting_id": 2,
                "group_ids": [],
                "user_id": 10,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/201",
            "fields": {
                "id": 201,
                "meeting_id": 1,
                "group_ids": [],
                "user_id": 20,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/202",
            "fields": {
                "id": 202,
                "meeting_id": 2,
                "group_ids": [],
                "user_id": 20,
            },
        },
    )

    finalize("0049_delete_removed_meeting_users")

    assert_model(
        "meeting/1",
        {
            "id": 1,
            "group_ids": [1],
            "meeting_user_ids": [101],
        },
    )
    assert_model(
        "meeting/2",
        {
            "id": 2,
            "group_ids": [2],
            "meeting_user_ids": [],
        },
    )
    assert_model(
        "group/1",
        {
            "id": 1,
            "meeting_id": 1,
            "meeting_user_ids": [101],
        },
    )
    assert_model(
        "group/2",
        {
            "id": 2,
            "meeting_id": 2,
            "meeting_user_ids": [],
        },
    )
    assert_model(
        "user/10",
        {
            "id": 10,
            "meeting_user_ids": [101],
        },
    )
    assert_model(
        "user/20",
        {
            "id": 20,
            "meeting_user_ids": [],
        },
    )
    assert_model(
        "meeting_user/101",
        {
            "id": 102,
            "meeting_id": 1,
            "group_ids": [1],
            "user_id": 10,
        },
    )

    assert_model(
        "meeting_user/102",
        {
            "id": 102,
            "meeting_id": 2,
            "group_ids": [],
            "user_id": 10,
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/201",
        {
            "id": 201,
            "meeting_id": 1,
            "group_ids": [],
            "user_id": 20,
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/202",
        {
            "id": 202,
            "meeting_id": 2,
            "group_ids": [],
            "user_id": 20,
            "meta_deleted": True,
        },
    )
