def setup_data(write):
    """Creates a meeting, a motion and a forwarding."""
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"name": "test", "motion_ids": [1]},
        },
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {"meeting_id": 1},
        },
    )
    write(
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {"meeting_id": 1, "origin_id": 1, "all_origin_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": [2], "all_derived_motion_ids": [2]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1, 2]},
        },
    )


def test_migration(write, finalize, assert_model):
    setup_data(write)
    write(
        {
            "type": "delete",
            "fqid": "motion/2",
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": []},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1]},
        },
    )
    finalize("0032_fix_motion_origin_relations")

    assert_model(
        "motion/2",
        {
            "meeting_id": 1,
            "origin_id": 1,
            "origin_meeting_id": 1,
            "all_origin_ids": [1],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "meeting/1",
        {
            "name": "test",
            "motion_ids": [1, 2],
            "forwarded_motion_ids": [2],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "motion/1",
        {
            "meeting_id": 1,
            "derived_motion_ids": [],
            "all_derived_motion_ids": [],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "meeting/1",
        {
            "name": "test",
            "motion_ids": [1],
            "forwarded_motion_ids": [],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )


def test_all_origin_ids(write, finalize, assert_model):
    setup_data(write)
    write(
        {
            "type": "delete",
            "fqid": "motion/1",
        },
        {
            "type": "update",
            "fqid": "motion/2",
            "fields": {"origin_id": None},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [2]},
        },
    )
    finalize("0032_fix_motion_origin_relations")

    assert_model(
        "motion/2",
        {
            "meeting_id": 1,
            "origin_meeting_id": 1,
            "all_origin_ids": [],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )


def test_deleted_created_motions(write, finalize, assert_model):
    setup_data(write)
    write(
        {
            "type": "delete",
            "fqid": "motion/2",
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": []},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1]},
        },
    )

    write(
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {"meeting_id": 1, "origin_id": 1, "all_origin_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": [3], "all_derived_motion_ids": [2, 3]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1, 3]},
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/1",
        },
        {
            "type": "update",
            "fqid": "motion/3",
            "fields": {"origin_id": None},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [3]},
        },
    )
    finalize("0032_fix_motion_origin_relations")

    assert_model(
        "motion/2",
        {
            "meeting_id": 1,
            "origin_id": 1,
            "origin_meeting_id": 1,
            "all_origin_ids": [1],
            "meta_deleted": True,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "motion/3",
        {
            "meeting_id": 1,
            "origin_id": 1,
            "origin_meeting_id": 1,
            "all_origin_ids": [1],
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )
    assert_model(
        "motion/1",
        {
            "meeting_id": 1,
            "derived_motion_ids": [3],
            "all_derived_motion_ids": [3],
            "meta_deleted": True,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "motion/3",
        {
            "meeting_id": 1,
            "origin_meeting_id": 1,
            "all_origin_ids": [],
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )


def test_deleted_motions(write, finalize, assert_model):
    setup_data(write)
    write(
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {"meeting_id": 1, "origin_id": 1, "all_origin_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": [2, 3], "all_derived_motion_ids": [2, 3]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1, 2, 3]},
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/2",
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": [3]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1, 3]},
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/1",
        },
        {
            "type": "update",
            "fqid": "motion/3",
            "fields": {"origin_id": None},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [3]},
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/3",
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": []},
        },
    )
    finalize("0032_fix_motion_origin_relations")

    assert_model(
        "motion/2",
        {
            "meeting_id": 1,
            "origin_id": 1,
            "origin_meeting_id": 1,
            "all_origin_ids": [1],
            "meta_deleted": True,
            "meta_position": 4,
        },
        position=4,
    )
    assert_model(
        "motion/1",
        {
            "meeting_id": 1,
            "derived_motion_ids": [3],
            "all_derived_motion_ids": [3],
            "meta_deleted": True,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "motion/3",
        {
            "meeting_id": 1,
            "all_origin_ids": [],
            "origin_meeting_id": 1,
            "meta_deleted": True,
            "meta_position": 6,
        },
        position=6,
    )


def test_multiple_forwarded_stages_customer_example(write, finalize, assert_model):
    setup_data(write)
    write(
        {
            "type": "delete",
            "fqid": "motion/2",
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": []},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1]},
        },
    )
    write(
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {"meeting_id": 1, "origin_id": 1, "all_origin_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": [3], "all_derived_motion_ids": [2, 3]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1, 3]},
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/3",
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": []},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1]},
        },
    )
    write(
        {
            "type": "create",
            "fqid": "motion/4",
            "fields": {"meeting_id": 1, "origin_id": 1, "all_origin_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"derived_motion_ids": [4], "all_derived_motion_ids": [2, 3, 4]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1, 4]},
        },
    )
    write(
        {
            "type": "create",
            "fqid": "motion/5",
            "fields": {"meeting_id": 1, "origin_id": 1, "all_origin_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {
                "derived_motion_ids": [4, 5],
                "all_derived_motion_ids": [2, 3, 4, 5],
            },
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1, 4, 5]},
        },
    )
    write(
        {
            "type": "create",
            "fqid": "motion/6",
            "fields": {"meeting_id": 1, "origin_id": 4, "all_origin_ids": [4, 1]},
        },
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {
                "derived_motion_ids": [4, 5],
                "all_derived_motion_ids": [2, 3, 4, 5, 6],
            },
        },
        {
            "type": "update",
            "fqid": "motion/4",
            "fields": {"derived_motion_ids": [6], "all_derived_motion_ids": [6]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1, 4, 5, 6]},
        },
    )
    write(
        {"type": "delete", "fqid": "motion/1"},
        {
            "type": "update",
            "fqid": "motion/4",
            "fields": {"origin_id": None},
        },
        {
            "type": "update",
            "fqid": "motion/5",
            "fields": {"origin_id": None},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [4, 5, 6]},
        },
    )

    finalize("0032_fix_motion_origin_relations")

    assert_model(
        "motion/1",
        {
            "meeting_id": 1,
            "derived_motion_ids": [4, 5],
            "all_derived_motion_ids": [4, 5, 6],
            "meta_deleted": True,
            "meta_position": 9,
        },
        position=9,
    )
    assert_model(
        "motion/2",
        {
            "meeting_id": 1,
            "origin_id": 1,
            "origin_meeting_id": 1,
            "all_origin_ids": [1],
            "meta_deleted": True,
            "meta_position": 3,
        },
        position=9,
    )
    assert_model(
        "motion/3",
        {
            "meeting_id": 1,
            "origin_id": 1,
            "all_origin_ids": [1],
            "origin_meeting_id": 1,
            "meta_deleted": True,
            "meta_position": 5,
        },
        position=9,
    )
    assert_model(
        "motion/4",
        {
            "meeting_id": 1,
            "derived_motion_ids": [6],
            "all_derived_motion_ids": [6],
            "all_origin_ids": [],
            "origin_meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 9,
        },
        position=9,
    )
    assert_model(
        "motion/5",
        {
            "meeting_id": 1,
            "all_origin_ids": [],
            "origin_meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 9,
        },
        position=9,
    )
    assert_model(
        "motion/6",
        {
            "meeting_id": 1,
            "origin_id": 4,
            "all_origin_ids": [4],
            "origin_meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 9,
        },
        position=9,
    )
