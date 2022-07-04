def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {"a": 1, "workflow_id": False},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"a": 2, "workflow_id": True},
        }
    )
    write({"type": "delete", "fqid": "motion/1"})
    write({"type": "restore", "fqid": "motion/1"})

    finalize("0015_remove_workflow_id")

    assert_model(
        "motion/1",
        {"a": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "motion/1",
        {"a": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "motion/1",
        {"a": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "motion/1",
        {"a": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
