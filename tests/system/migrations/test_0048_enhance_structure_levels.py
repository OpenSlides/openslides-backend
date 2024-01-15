def test_migration(write, finalize, assert_model):
    write(
        # user with default_structure_level
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {
                "id": 1,
                "default_structure_level": "default",
                "meeting_user_ids": [11, 12, 13],
            },
        },
        # user without default_structure_level
        {
            "type": "create",
            "fqid": "user/2",
            "fields": {"id": 2, "meeting_user_ids": [21, 22]},
        },
        # meetings
        {
            "type": "create",
            "fqid": "meeting/42",
            "fields": {"id": 42, "meeting_user_ids": [11, 13, 21, 22]},
        },
        {
            "type": "create",
            "fqid": "meeting/43",
            "fields": {"id": 43, "meeting_user_ids": [12]},
        },
        # meeting_user with structure_level and default_structure_level
        {
            "type": "create",
            "fqid": "meeting_user/11",
            "fields": {
                "id": 11,
                "user_id": 1,
                "meeting_id": 42,
                "structure_level": "level",
            },
        },
        # meeting_user in other meeting with structure_level and default_structure_level
        {
            "type": "create",
            "fqid": "meeting_user/12",
            "fields": {
                "id": 12,
                "user_id": 1,
                "meeting_id": 43,
                "structure_level": "level",
            },
        },
        # meeting_user with structure_level, but without default_structure_level
        {
            "type": "create",
            "fqid": "meeting_user/21",
            "fields": {
                "id": 21,
                "user_id": 2,
                "meeting_id": 42,
                "structure_level": "level",
            },
        },
        # meeting_user without structure_level, but with default_structure_level
        {
            "type": "create",
            "fqid": "meeting_user/13",
            "fields": {"id": 13, "user_id": 1, "meeting_id": 42},
        },
        # meeting_user without structure_level and without default_structure_level
        {
            "type": "create",
            "fqid": "meeting_user/22",
            "fields": {"id": 22, "user_id": 2, "meeting_id": 42},
        },
    )
    finalize("0048_enhance_structure_levels")

    assert_model(
        "user/1",
        {
            "id": 1,
            "meeting_user_ids": [11, 12, 13],
        },
    )
    assert_model(
        "user/2",
        {
            "id": 2,
            "meeting_user_ids": [21, 22],
        },
    )
    assert_model(
        "structure_level/1",
        {"id": 1, "meeting_id": 42, "name": "level", "meeting_user_ids": [11, 21]},
    )
    assert_model(
        "structure_level/2",
        {"id": 2, "meeting_id": 43, "name": "level", "meeting_user_ids": [12]},
    )
    assert_model(
        "structure_level/3",
        {"id": 3, "meeting_id": 42, "name": "default", "meeting_user_ids": [13]},
    )
    assert_model(
        "meeting_user/11",
        {"id": 11, "user_id": 1, "meeting_id": 42, "structure_level_ids": [1]},
    )
    assert_model(
        "meeting_user/12",
        {"id": 12, "user_id": 1, "meeting_id": 43, "structure_level_ids": [2]},
    )
    assert_model(
        "meeting_user/13",
        {"id": 13, "user_id": 1, "meeting_id": 42, "structure_level_ids": [3]},
    )
    assert_model(
        "meeting_user/21",
        {"id": 21, "user_id": 2, "meeting_id": 42, "structure_level_ids": [1]},
    )
    assert_model(
        "meeting_user/22",
        {"id": 22, "user_id": 2, "meeting_id": 42},
    )
    assert_model(
        "meeting/42",
        {"id": 42, "meeting_user_ids": [11, 13, 21, 22], "structure_level_ids": [1, 3]},
    )
    assert_model(
        "meeting/43",
        {"id": 43, "meeting_user_ids": [12], "structure_level_ids": [2]},
    )


def test_no_events(write, finalize):
    write(
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {"id": 1, "meeting_user_ids": [11]},
        },
        {
            "type": "create",
            "fqid": "meeting/42",
            "fields": {"id": 42, "meeting_user_ids": [11]},
        },
        {
            "type": "create",
            "fqid": "meeting_user/11",
            "fields": {"id": 11, "user_id": 1, "meeting_id": 42},
        },
    )
    finalize("0048_enhance_structure_levels")
