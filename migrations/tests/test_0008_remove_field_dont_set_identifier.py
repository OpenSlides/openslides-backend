def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "motion_state/1",
            "fields": {"a": 1, "dont_set_identifier": False},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "motion_state/1",
            "fields": {"a": 2, "dont_set_identifier": True},
        }
    )
    write({"type": "delete", "fqid": "motion_state/1"})
    write({"type": "restore", "fqid": "motion_state/1"})

    finalize("0008_remove_field_dont_set_identifier")

    assert_model(
        "motion_state/1",
        {"a": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "motion_state/1",
        {"a": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "motion_state/1",
        {"a": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "motion_state/1",
        {"a": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
