def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": "meeting/1", "fields": {"id": 1}})
    write(
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {"id": 1, "sort_children_ids": [1], "sort_parent_id": 1},
        }
    )

    finalize("0028_rename_motion_sort_children_ids")

    assert_model(
        "motion/1",
        {
            "id": 1,
            "sort_child_ids": [1],
            "sort_parent_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
