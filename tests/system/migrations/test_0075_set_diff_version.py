def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {"id": 1, "amendment_ids": [3]},
        },
        {"type": "create", "fqid": "motion/2", "fields": {"id": 2}},
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {"id": 3, "lead_motion_id": 1},
        },
    )
    write(
        {"type": "delete", "fqid": "motion/2", "fields": {}},
    )

    finalize("0075_set_diff_version")

    assert_model(
        "motion/1",
        {"id": 1, "diff_version": "0.1.2", "amendment_ids": [3], "meta_deleted": False},
    )
    assert_model("motion/2", {"id": 2, "meta_deleted": True})
    assert_model("motion/3", {"id": 3, "lead_motion_id": 1, "meta_deleted": False})
