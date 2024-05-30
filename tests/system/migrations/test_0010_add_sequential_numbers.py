from openslides_backend.shared.patterns import fqid_from_collection_and_id

COLLECTIONS = (
    "assignment",
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
    for collection in COLLECTIONS:
        write(
            {
                "type": "create",
                "fqid": "meeting/1",
                "fields": {"id": 1, collection + "_ids": [1]},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "1"),
                "fields": {"id": 1, "meeting_id": 1},
            },
        )
        write(
            {
                "type": "update",
                "fqid": "meeting/1",
                "fields": {collection + "_ids": [1, 2]},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "2"),
                "fields": {"id": 2, "meeting_id": 1},
            },
        )

        finalize("0010_add_sequential_numbers")

        assert_model(
            fqid_from_collection_and_id(collection, "1"),
            {
                "id": 1,
                "sequential_number": 1,
                "meeting_id": 1,
                "meta_deleted": False,
                "meta_position": 1,
            },
        )
        assert_model(
            fqid_from_collection_and_id(collection, "2"),
            {
                "id": 2,
                "sequential_number": 2,
                "meeting_id": 1,
                "meta_deleted": False,
                "meta_position": 2,
            },
        )


def test_migration_motion_block_more_objects(write, finalize, assert_model):
    for collection in COLLECTIONS:
        write(
            {
                "type": "create",
                "fqid": "meeting/1",
                "fields": {"id": 1, collection + "_ids": [1]},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "1"),
                "fields": {"id": 1, "meeting_id": 1},
            },
        )
        write(
            {
                "type": "update",
                "fqid": "meeting/1",
                "fields": {collection + "_ids": [1, 2]},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "2"),
                "fields": {"id": 2, "meeting_id": 1},
            },
        )
        write(
            {
                "type": "create",
                "fqid": "meeting/2",
                "fields": {"id": 2, collection + "_ids": [3]},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "3"),
                "fields": {"id": 3, "meeting_id": 2},
            },
        )
        write(
            {
                "type": "update",
                "fqid": "meeting/2",
                "fields": {collection + "_ids": [3, 4]},
            },
            {
                "type": "create",
                "fqid": fqid_from_collection_and_id(collection, "4"),
                "fields": {"id": 4, "meeting_id": 2},
            },
        )

        finalize("0010_add_sequential_numbers")

        assert_model(
            fqid_from_collection_and_id(collection, "1"),
            {
                "id": 1,
                "sequential_number": 1,
                "meeting_id": 1,
                "meta_deleted": False,
                "meta_position": 1,
            },
        )
        assert_model(
            fqid_from_collection_and_id(collection, "2"),
            {
                "id": 2,
                "sequential_number": 2,
                "meeting_id": 1,
                "meta_deleted": False,
                "meta_position": 2,
            },
        )
        assert_model(
            fqid_from_collection_and_id(collection, "3"),
            {
                "id": 3,
                "sequential_number": 1,
                "meeting_id": 2,
                "meta_deleted": False,
                "meta_position": 3,
            },
        )

        assert_model(
            fqid_from_collection_and_id(collection, "4"),
            {
                "id": 4,
                "sequential_number": 2,
                "meeting_id": 2,
                "meta_deleted": False,
                "meta_position": 4,
            },
        )


def test_assignment_two_stages(migrate, write, finalize, assert_model):
    write({"type": "create", "fqid": "meeting/1", "fields": {"id": 1}})
    write({"type": "create", "fqid": "meeting/2", "fields": {"id": 2}})
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"id": 1, "assignment_ids": [1]},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "1"),
            "fields": {"id": 1, "meeting_id": 1},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"assignment_ids": [1, 2]},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "2"),
            "fields": {"id": 2, "meeting_id": 1},
        },
    )
    migrate("0010_add_sequential_numbers")
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"assignment_ids": [1, 2, 3]},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "3"),
            "fields": {"id": 3, "meeting_id": 1},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"assignment_ids": [1, 2, 3, 4]},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "4"),
            "fields": {"id": 4, "meeting_id": 1},
        },
    )

    finalize("0010_add_sequential_numbers")

    assert_model(
        fqid_from_collection_and_id("assignment", "1"),
        {
            "id": 1,
            "sequential_number": 1,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 3,
        },
    )
    assert_model(
        fqid_from_collection_and_id("assignment", "2"),
        {
            "id": 2,
            "sequential_number": 2,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 4,
        },
    )
    assert_model(
        fqid_from_collection_and_id("assignment", "3"),
        {
            "id": 3,
            "sequential_number": 3,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 5,
        },
    )

    assert_model(
        fqid_from_collection_and_id("assignment", "4"),
        {
            "id": 4,
            "sequential_number": 4,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 6,
        },
    )


def test_assignment_only_2_position(migrate, write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"id": 1, "assignment_ids": [1]},
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {"id": 2, "assignment_ids": [2, 3]},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "1"),
            "fields": {"id": 1, "meeting_id": 1},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "2"),
            "fields": {"id": 2, "meeting_id": 2},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "3"),
            "fields": {"id": 3, "meeting_id": 2},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"assignment_ids": [1, 4, 5]},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "4"),
            "fields": {"id": 4, "meeting_id": 1},
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("assignment", "5"),
            "fields": {"id": 5, "meeting_id": 1},
        },
    )

    finalize("0010_add_sequential_numbers")

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
            "sequential_number": 1,
            "meeting_id": 2,
            "meta_deleted": False,
            "meta_position": 1,
        },
    )
    assert_model(
        fqid_from_collection_and_id("assignment", "3"),
        {
            "id": 3,
            "sequential_number": 2,
            "meeting_id": 2,
            "meta_deleted": False,
            "meta_position": 1,
        },
    )

    assert_model(
        fqid_from_collection_and_id("assignment", "4"),
        {
            "id": 4,
            "sequential_number": 2,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
    )

    assert_model(
        fqid_from_collection_and_id("assignment", "5"),
        {
            "id": 5,
            "sequential_number": 3,
            "meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
    )
