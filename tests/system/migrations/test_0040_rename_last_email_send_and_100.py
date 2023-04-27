def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "a": 1,
                "motion_poll_default_100_percent_base": "90",
                "assignment_poll_default_100_percent_base": "50",
                "poll_default_100_percent_base": "30",
            },
        },
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {"b": 1, "last_email_send": 100000},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {
                "a": 2,
                "motion_poll_default_100_percent_base": "95",
                "assignment_poll_default_100_percent_base": "55",
                "poll_default_100_percent_base": "35",
            },
        },
        {
            "type": "update",
            "fqid": "user/1",
            "fields": {"b": 2, "last_email_send": 150000},
        },
    )
    write({"type": "delete", "fqid": "meeting/1"}, {"type": "delete", "fqid": "user/1"})
    write(
        {"type": "restore", "fqid": "meeting/1"}, {"type": "restore", "fqid": "user/1"}
    )

    finalize("0040_rename_last_email_send_and_100")

    assert_model(
        "meeting/1",
        {
            "a": 1,
            "meta_deleted": False,
            "meta_position": 1,
            "motion_poll_default_onehundred_percent_base": "90",
            "assignment_poll_default_onehundred_percent_base": "50",
            "poll_default_onehundred_percent_base": "30",
        },
        position=1,
    )
    assert_model(
        "user/1",
        {"b": 1, "last_email_sent": 100000, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "meeting/1",
        {
            "a": 2,
            "meta_deleted": False,
            "meta_position": 2,
            "motion_poll_default_onehundred_percent_base": "95",
            "assignment_poll_default_onehundred_percent_base": "55",
            "poll_default_onehundred_percent_base": "35",
        },
        position=2,
    )
    assert_model(
        "user/1",
        {"b": 2, "last_email_sent": 150000, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "meeting/1",
        {
            "a": 2,
            "meta_deleted": True,
            "meta_position": 3,
            "motion_poll_default_onehundred_percent_base": "95",
            "assignment_poll_default_onehundred_percent_base": "55",
            "poll_default_onehundred_percent_base": "35",
        },
        position=3,
    )
    assert_model(
        "user/1",
        {"b": 2, "last_email_sent": 150000, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "meeting/1",
        {
            "a": 2,
            "meta_deleted": False,
            "meta_position": 4,
            "motion_poll_default_onehundred_percent_base": "95",
            "assignment_poll_default_onehundred_percent_base": "55",
            "poll_default_onehundred_percent_base": "35",
        },
        position=4,
    )
    assert_model(
        "user/1",
        {"b": 2, "last_email_sent": 150000, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
