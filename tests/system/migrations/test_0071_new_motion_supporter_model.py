def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "id": 1,
                "motion_ids": [101, 102, 103],
                "meeting_user_ids": [11, 21, 31],
            },
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {
                "id": 2,
                "motion_ids": [201, 202, 203, 204],
                "meeting_user_ids": [12, 22, 32],
            },
        },
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {
                "id": 1,
                "meeting_user_ids": [11, 12],
            },
        },
        {
            "type": "create",
            "fqid": "user/2",
            "fields": {
                "id": 2,
                "meeting_user_ids": [21, 22],
            },
        },
        {
            "type": "create",
            "fqid": "user/3",
            "fields": {
                "id": 3,
                "meeting_user_ids": [31, 32],
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/11",
            "fields": {
                "id": 11,
                "user_id": 1,
                "meeting_id": 1,
                "supported_motion_ids": [101, 102, 103],
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/12",
            "fields": {
                "id": 12,
                "user_id": 1,
                "meeting_id": 2,
                "supported_motion_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/21",
            "fields": {
                "id": 21,
                "user_id": 2,
                "meeting_id": 1,
                "supported_motion_ids": [101],
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/22",
            "fields": {
                "id": 22,
                "user_id": 2,
                "meeting_id": 2,
                "supported_motion_ids": None,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/31",
            "fields": {
                "id": 31,
                "user_id": 3,
                "meeting_id": 1,
                "supported_motion_ids": [101],
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/32",
            "fields": {
                "id": 32,
                "user_id": 3,
                "meeting_id": 2,
                "supported_motion_ids": [201],
            },
        },
        {
            "type": "create",
            "fqid": "motion/101",
            "fields": {
                "id": 101,
                "meeting_id": 1,
                "supporter_meeting_user_ids": [11, 21, 31],
            },
        },
        {
            "type": "create",
            "fqid": "motion/102",
            "fields": {"id": 102, "meeting_id": 1, "supporter_meeting_user_ids": [11]},
        },
        {
            "type": "create",
            "fqid": "motion/103",
            "fields": {"id": 103, "meeting_id": 1, "supporter_meeting_user_ids": [11]},
        },
        {
            "type": "create",
            "fqid": "motion/201",
            "fields": {"id": 201, "meeting_id": 2, "supporter_meeting_user_ids": [32]},
        },
        {
            "type": "create",
            "fqid": "motion/202",
            "fields": {"id": 202, "meeting_id": 2, "supporter_meeting_user_ids": []},
        },
        {
            "type": "create",
            "fqid": "motion/203",
            "fields": {"id": 203, "meeting_id": 2, "supporter_meeting_user_ids": None},
        },
        {
            "type": "create",
            "fqid": "motion/204",
            "fields": {
                "id": 203,
                "meeting_id": 2,
            },
        },
    )
    write(
        {"type": "delete", "fqid": "motion/103"},
        {
            "type": "update",
            "fqid": "meeting/1",
            "list_fields": {
                "remove": {"motion_ids": [103]},
            },
        },
        {
            "type": "update",
            "fqid": "meeting_user/11",
            "list_fields": {
                "remove": {"supported_motion_ids": [103]},
            },
        },
    )

    finalize("0071_new_motion_supporter_model")

    assert_model(
        "meeting/1",
        {
            "id": 1,
            "motion_ids": [101, 102],
            "meeting_user_ids": [11, 21, 31],
            "motion_supporter_ids": [1, 2, 3, 4],
        },
    )
    assert_model(
        "meeting/2",
        {
            "id": 2,
            "motion_ids": [201, 202, 203, 204],
            "meeting_user_ids": [12, 22, 32],
            "motion_supporter_ids": [5],
        },
    )

    assert_model(
        "meeting_user/11",
        {"id": 11, "user_id": 1, "meeting_id": 1, "motion_supporter_ids": [1, 4]},
    )
    assert_model(
        "meeting_user/12",
        {
            "id": 12,
            "user_id": 1,
            "meeting_id": 2,
        },
    )
    assert_model(
        "meeting_user/21",
        {"id": 21, "user_id": 2, "meeting_id": 1, "motion_supporter_ids": [2]},
    )
    assert_model(
        "meeting_user/22",
        {
            "id": 22,
            "user_id": 2,
            "meeting_id": 2,
        },
    )
    assert_model(
        "meeting_user/31",
        {"id": 31, "user_id": 3, "meeting_id": 1, "motion_supporter_ids": [3]},
    )
    assert_model(
        "meeting_user/32",
        {"id": 32, "user_id": 3, "meeting_id": 2, "motion_supporter_ids": [5]},
    )

    assert_model(
        "motion_supporter/1",
        {"id": 1, "meeting_id": 1, "meeting_user_id": 11, "motion_id": 101},
    )
    assert_model(
        "motion_supporter/2",
        {"id": 2, "meeting_id": 1, "meeting_user_id": 21, "motion_id": 101},
    )
    assert_model(
        "motion_supporter/3",
        {"id": 3, "meeting_id": 1, "meeting_user_id": 31, "motion_id": 101},
    )
    assert_model(
        "motion_supporter/4",
        {"id": 4, "meeting_id": 1, "meeting_user_id": 11, "motion_id": 102},
    )
    assert_model(
        "motion_supporter/5",
        {"id": 5, "meeting_id": 2, "meeting_user_id": 32, "motion_id": 201},
    )

    assert_model("motion/101", {"id": 101, "meeting_id": 1, "supporter_ids": [1, 2, 3]})
    assert_model("motion/102", {"id": 102, "meeting_id": 1, "supporter_ids": [4]})
    assert_model("motion/201", {"id": 201, "meeting_id": 2, "supporter_ids": [5]})
    assert_model("motion/202", {"id": 202, "meeting_id": 2, "supporter_ids": []})
    assert_model(
        "motion/203",
        {
            "id": 203,
            "meeting_id": 2,
        },
    )
    assert_model(
        "motion/204",
        {
            "id": 203,
            "meeting_id": 2,
        },
    )

    assert_model(
        "motion/103",
        {
            "id": 103,
            "meeting_id": 1,
            "supporter_meeting_user_ids": [11],
            "meta_deleted": True,
        },
    )
