def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {
                "id": 1,
                "default_number": "WeAreNumberOne",
            },
        },
    )
    write(
        {
            "type": "create",
            "fqid": "user/2",
            "fields": {
                "id": 2,
                "default_number": "",
            },
        },
    )
    write(
        {
            "type": "create",
            "fqid": "user/3",
            "fields": {
                "id": 3,
            },
        },
    )

    finalize("0051_remove_default_numbers")

    assert_model(
        "user/1",
        {
            "id": 1,
        },
    )
    assert_model(
        "user/2",
        {
            "id": 2,
        },
    )
    assert_model(
        "user/3",
        {
            "id": 3,
        },
    )
