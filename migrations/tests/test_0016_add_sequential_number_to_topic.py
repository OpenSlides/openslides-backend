def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": "meeting/1", "fields": {"id": 1}})
    write({"type": "create", "fqid": "topic/1", "fields": {"id": 1, "meeting_id": 1}})
    write({"type": "create", "fqid": "topic/2", "fields": {"id": 2, "meeting_id": 1}})

    finalize("0016_add_sequential_number_to_topic")

    assert_model(
        "topic/1",
        {
            "id": 1,
            "sequential_number": 1,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
    )
    assert_model(
        "topic/2",
        {
            "id": 2,
            "sequential_number": 2,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 3,
        },
    )


def test_migration_more_objects(write, finalize, assert_model):
    write({"type": "create", "fqid": "meeting/1", "fields": {"id": 1}})
    write({"type": "create", "fqid": "meeting/2", "fields": {"id": 2}})
    write({"type": "create", "fqid": "topic/1", "fields": {"id": 1, "meeting_id": 1}})
    write({"type": "create", "fqid": "topic/2", "fields": {"id": 2, "meeting_id": 1}})
    write({"type": "create", "fqid": "topic/3", "fields": {"id": 3, "meeting_id": 2}})
    write({"type": "create", "fqid": "topic/4", "fields": {"id": 4, "meeting_id": 2}})

    finalize("0016_add_sequential_number_to_topic")

    assert_model(
        "topic/1",
        {
            "id": 1,
            "sequential_number": 1,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 3,
        },
    )
    assert_model(
        "topic/2",
        {
            "id": 2,
            "sequential_number": 2,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 4,
        },
    )
    assert_model(
        "topic/3",
        {
            "id": 3,
            "sequential_number": 1,
            "meeting_id": 2,
            "meta_deleted": False,
            "meta_position": 5,
        },
    )

    assert_model(
        "topic/4",
        {
            "id": 4,
            "sequential_number": 2,
            "meeting_id": 2,
            "meta_deleted": False,
            "meta_position": 6,
        },
    )
