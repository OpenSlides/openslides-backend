def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": "meeting/1", "fields": {"id": 1}})
    write(
        {
            "type": "create",
            "fqid": "list_of_speakers/1",
            "fields": {"id": 1, "meeting_id": 1},
        }
    )
    write(
        {
            "type": "create",
            "fqid": "list_of_speakers/2",
            "fields": {"id": 2, "meeting_id": 1},
        }
    )

    finalize("0017_add_sequential_number_to_list_of_speakers")

    assert_model(
        "list_of_speakers/1",
        {
            "id": 1,
            "sequential_number": 1,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
    )
    assert_model(
        "list_of_speakers/2",
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
    write(
        {
            "type": "create",
            "fqid": "list_of_speakers/1",
            "fields": {"id": 1, "meeting_id": 1},
        }
    )
    write(
        {
            "type": "create",
            "fqid": "list_of_speakers/2",
            "fields": {"id": 2, "meeting_id": 1},
        }
    )
    write(
        {
            "type": "create",
            "fqid": "list_of_speakers/3",
            "fields": {"id": 3, "meeting_id": 2},
        }
    )
    write(
        {
            "type": "create",
            "fqid": "list_of_speakers/4",
            "fields": {"id": 4, "meeting_id": 2},
        }
    )

    finalize("0017_add_sequential_number_to_list_of_speakers")

    assert_model(
        "list_of_speakers/1",
        {
            "id": 1,
            "sequential_number": 1,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 3,
        },
    )
    assert_model(
        "list_of_speakers/2",
        {
            "id": 2,
            "sequential_number": 2,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 4,
        },
    )
    assert_model(
        "list_of_speakers/3",
        {
            "id": 3,
            "sequential_number": 1,
            "meeting_id": 2,
            "meta_deleted": False,
            "meta_position": 5,
        },
    )

    assert_model(
        "list_of_speakers/4",
        {
            "id": 4,
            "sequential_number": 2,
            "meeting_id": 2,
            "meta_deleted": False,
            "meta_position": 6,
        },
    )
