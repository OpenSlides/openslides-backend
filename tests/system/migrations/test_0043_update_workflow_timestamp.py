def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {
                "a": 1,
                "created": 1686740704,
            },
        },
        {
            "type": "create",
            "fqid": "motion_state/1",
            "fields": {"b": 1, "set_created_timestamp": True},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {
                "a": 2,
                "created": 1686740814,
            },
        },
        {
            "type": "update",
            "fqid": "motion_state/1",
            "fields": {"b": 2, "set_created_timestamp": False},
        },
    )
    write(
        {"type": "delete", "fqid": "motion/1"},
        {"type": "delete", "fqid": "motion_state/1"},
    )
    write(
        {"type": "restore", "fqid": "motion/1"},
        {"type": "restore", "fqid": "motion_state/1"},
    )

    finalize("0043_update_workflow_timestamp")

    assert_model(
        "motion/1",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "a": 1,
            "created": 1686740704,
            "workflow_timestamp": 1686740704,
        },
        position=1,
    )
    assert_model(
        "motion_state/1",
        {
            "b": 1,
            "set_workflow_timestamp": True,
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        "motion/1",
        {
            "meta_deleted": False,
            "meta_position": 2,
            "a": 2,
            "created": 1686740814,
            "workflow_timestamp": 1686740814,
        },
        position=2,
    )
    assert_model(
        "motion_state/1",
        {
            "b": 2,
            "set_workflow_timestamp": False,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "motion/1",
        {
            "meta_deleted": True,
            "meta_position": 3,
            "a": 2,
            "created": 1686740814,
            "workflow_timestamp": 1686740814,
        },
        position=3,
    )
    assert_model(
        "motion_state/1",
        {
            "b": 2,
            "set_workflow_timestamp": False,
            "meta_deleted": True,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "motion/1",
        {
            "meta_deleted": False,
            "meta_position": 4,
            "a": 2,
            "created": 1686740814,
            "workflow_timestamp": 1686740814,
        },
        position=4,
    )
    assert_model(
        "motion_state/1",
        {
            "b": 2,
            "set_workflow_timestamp": False,
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )
