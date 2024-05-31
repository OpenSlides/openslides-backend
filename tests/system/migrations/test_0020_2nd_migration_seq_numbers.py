from openslides_backend.shared.patterns import fqid_from_collection_and_id

COLLECTIONS = (
    "assignment",
    "motion",
    "motion_block",
    "motion_category",
    "motion_workflow",
    "poll",
    "projector",
    "topic",
    "list_of_speakers",
    "motion_statute_paragraph",
    "motion_comment_section",
)


def test_migration_all(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"id": 1},
        },
    )
    for i, collection in enumerate(COLLECTIONS, start=2):
        write(
            {
                "type": "update",
                "fqid": "meeting/1",
                "fields": {"id": 1, collection + "_ids": [1, 2]},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "1"),
                "fields": {"id": 1, "meeting_id": 1, "sequential_number": 1},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "2"),
                "fields": {"id": 2, "meeting_id": 1, "sequential_number": 1},
            },
        )

        finalize("0020_2nd_migration_seq_numbers")

        assert_model(
            fqid_from_collection_and_id(collection, "1"),
            {
                "id": 1,
                "sequential_number": 1,
                "meeting_id": 1,
                "meta_deleted": False,
                "meta_position": i,
            },
        )
        assert_model(
            fqid_from_collection_and_id(collection, "2"),
            {
                "id": 2,
                "sequential_number": 2,
                "meeting_id": 1,
                "meta_deleted": False,
                "meta_position": i,
            },
        )


def test_migration_motion_block_more_objects(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"id": 1},
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {"id": 2},
        },
    )
    for i, collection in enumerate(COLLECTIONS, start=2):
        write(
            {
                "type": "update",
                "fqid": "meeting/1",
                "fields": {"id": 1, collection + "_ids": [1, 2]},
            },
            {
                "type": "update",
                "fqid": "meeting/2",
                "fields": {"id": 2, collection + "_ids": [3, 4]},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "1"),
                "fields": {"id": 1, "meeting_id": 1, "sequential_number": 1},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "2"),
                "fields": {"id": 2, "meeting_id": 1, "sequential_number": 1},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "3"),
                "fields": {"id": 3, "meeting_id": 2, "sequential_number": 1},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "4"),
                "fields": {"id": 4, "meeting_id": 2, "sequential_number": 1},
            },
        )

        finalize("0020_2nd_migration_seq_numbers")

        assert_model(
            fqid_from_collection_and_id(collection, "1"),
            {
                "id": 1,
                "sequential_number": 1,
                "meeting_id": 1,
                "meta_deleted": False,
                "meta_position": i,
            },
        )
        assert_model(
            fqid_from_collection_and_id(collection, "2"),
            {
                "id": 2,
                "sequential_number": 2,
                "meeting_id": 1,
                "meta_deleted": False,
                "meta_position": i,
            },
        )
        assert_model(
            fqid_from_collection_and_id(collection, "3"),
            {
                "id": 3,
                "sequential_number": 1,
                "meeting_id": 2,
                "meta_deleted": False,
                "meta_position": i,
            },
        )

        assert_model(
            fqid_from_collection_and_id(collection, "4"),
            {
                "id": 4,
                "sequential_number": 2,
                "meeting_id": 2,
                "meta_deleted": False,
                "meta_position": i,
            },
        )


def test_assignment_two_stages(migrate, write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"id": 1, "assignment_ids": [1, 2]},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "1"),
            "fields": {"id": 1, "meeting_id": 1, "sequential_number": 11},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "2"),
            "fields": {"id": 2, "meeting_id": 1, "sequential_number": 12},
        },
    )
    migrate("0020_2nd_migration_seq_numbers")
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"assignment_ids": [1, 2, 3, 4]},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "3"),
            "fields": {"id": 3, "meeting_id": 1, "sequential_number": 13},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "4"),
            "fields": {"id": 4, "meeting_id": 1, "sequential_number": 14},
        },
    )

    finalize("0020_2nd_migration_seq_numbers")

    assert_model(
        fqid_from_collection_and_id("assignment", "1"),
        {
            "id": 1,
            "sequential_number": 1,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 1,
        },
    )
    assert_model(
        fqid_from_collection_and_id("assignment", "2"),
        {
            "id": 2,
            "sequential_number": 2,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 1,
        },
    )
    assert_model(
        fqid_from_collection_and_id("assignment", "3"),
        {
            "id": 3,
            "sequential_number": 3,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
    )

    assert_model(
        fqid_from_collection_and_id("assignment", "4"),
        {
            "id": 4,
            "sequential_number": 4,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
    )
