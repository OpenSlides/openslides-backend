def test_migration_full(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"id": 1, "motion_poll_default_method": None},
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {"id": 2, "motion_poll_default_method": "YN"},
        },
    )

    finalize("0058_fix_motion_poll_default_method")

    assert_model(
        "meeting/1",
        {"id": 1, "motion_poll_default_method": "YNA"},
    )
    assert_model(
        "meeting/2",
        {"id": 2, "motion_poll_default_method": "YN"},
    )
