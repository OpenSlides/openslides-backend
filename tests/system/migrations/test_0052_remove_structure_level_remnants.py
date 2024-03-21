def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting_user/1",
            "fields": {
                "id": 1,
                "structure_level": "WeAreNumberOne",
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/2",
            "fields": {
                "id": 2,
                "structure_level": "",
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/3",
            "fields": {
                "id": 3,
            },
        },
    )

    finalize("0052_remove_structure_level_remnants")

    assert_model(
        "meeting_user/1",
        {
            "id": 1,
        },
    )
    assert_model(
        "meeting_user/2",
        {
            "id": 2,
        },
    )
    assert_model(
        "meeting_user/3",
        {
            "id": 3,
        },
    )
