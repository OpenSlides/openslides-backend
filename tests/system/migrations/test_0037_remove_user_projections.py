from tests.system.migrations.conftest import DoesNotExist


def test_migration(write, finalize, assert_model):
    # setup data
    write(
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {"username": "test"},
        },
        {
            "type": "create",
            "fqid": "projector/2",
            "fields": {"meeting_id": 1},
        },
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1], "projector_ids": [2]},
        },
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {"meeting_id": 1},
        },
    )

    # projector.project a user
    write(
        {
            "type": "create",
            "fqid": "projection/5",
            "fields": {
                "meeting_id": 1,
                "current_projector_id": 2,
                "content_object_id": "user/1",
            },
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {"current_projection_ids": [5]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"all_projection_ids": [5]},
        },
        {
            "type": "update",
            "fqid": "user/1",
            "fields": {"projection_$1_ids": [5], "projection_$_ids": ["1"]},
        },
    )

    # projector.project something else
    write(
        {
            "type": "create",
            "fqid": "projection/6",
            "fields": {
                "meeting_id": 1,
                "current_projector_id": 2,
                "content_object_id": "motion/1",
            },
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {
                "current_projection_ids": [6],
                "history_projection_ids": [5],
            },
        },
        {
            "type": "update",
            "fqid": "projection/5",
            "fields": {
                "current_projector_id": None,
                "history_projector_id": 2,
            },
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"all_projection_ids": [5, 6]},
        },
        {"type": "update", "fqid": "motion/1", "fields": {"projection_ids": [6]}},
    )

    # projector.add_to_preview a user
    write(
        {
            "type": "create",
            "fqid": "projection/7",
            "fields": {
                "meeting_id": 1,
                "preview_projector_id": 2,
                "content_object_id": "user/1",
            },
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"all_projection_ids": [5, 6, 7]},
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {"preview_projection_ids": [7]},
        },
        {"type": "update", "fqid": "user/1", "fields": {"projection_$1_ids": [5, 7]}},
    )

    # projector.next: switch to the user projection
    write(
        {
            "type": "update",
            "fqid": "projection/6",
            "fields": {
                "current_projector_id": None,
                "history_projector_id": 2,
            },
        },
        {
            "type": "update",
            "fqid": "projection/7",
            "fields": {"current_projector_id": 2, "preview_projector_id": None},
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {
                "current_projection_ids": [7],
                "preview_projection_ids": [],
                "history_projection_ids": [5, 6],
            },
        },
    )

    # projector.add_to_preview something else
    write(
        {
            "type": "create",
            "fqid": "projection/8",
            "fields": {
                "meeting_id": 1,
                "preview_projector_id": 2,
                "content_object_id": "motion/1",
            },
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"all_projection_ids": [5, 6, 7, 8]},
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {"preview_projection_ids": [8]},
        },
        {"type": "update", "fqid": "motion/1", "fields": {"projection_ids": [6, 8]}},
    )

    # projector.next: switch to the other projection
    write(
        {
            "type": "update",
            "fqid": "projection/7",
            "fields": {
                "current_projector_id": None,
                "history_projector_id": 2,
            },
        },
        {
            "type": "update",
            "fqid": "projection/8",
            "fields": {"current_projector_id": 2, "preview_projector_id": None},
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {
                "current_projection_ids": [8],
                "preview_projection_ids": [],
                "history_projection_ids": [5, 6, 7],
            },
        },
    )

    # projector.previous: back to the user projection
    write(
        {
            "type": "update",
            "fqid": "projection/8",
            "fields": {
                "current_projector_id": None,
                "preview_projector_id": 2,
            },
        },
        {
            "type": "update",
            "fqid": "projection/7",
            "fields": {"current_projector_id": 2, "history_projector_id": None},
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {
                "current_projection_ids": [7],
                "preview_projection_ids": [8],
                "history_projection_ids": [5, 6],
            },
        },
    )

    # projector.previous: back to something else, user projection is in queue again
    write(
        {
            "type": "update",
            "fqid": "projection/7",
            "fields": {
                "current_projector_id": None,
                "preview_projector_id": 2,
            },
        },
        {
            "type": "update",
            "fqid": "projection/6",
            "fields": {"current_projector_id": 2, "history_projector_id": None},
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {
                "current_projection_ids": [6],
                "preview_projection_ids": [7, 8],
                "history_projection_ids": [5],
            },
        },
    )

    # projector.add_to_preview a user again
    write(
        {
            "type": "create",
            "fqid": "projection/9",
            "fields": {
                "meeting_id": 1,
                "preview_projector_id": 2,
                "content_object_id": "user/1",
            },
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"all_projection_ids": [5, 6, 7, 8, 9]},
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {"preview_projection_ids": [7, 8, 9]},
        },
        {
            "type": "update",
            "fqid": "user/1",
            "fields": {"projection_$1_ids": [5, 7, 9]},
        },
    )

    # projector.project_preview: specifically project the new user projection
    write(
        {
            "type": "update",
            "fqid": "projection/6",
            "fields": {
                "current_projector_id": None,
                "history_projector_id": 2,
            },
        },
        {
            "type": "update",
            "fqid": "projection/9",
            "fields": {"current_projector_id": 2, "preview_projector_id": None},
        },
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {
                "current_projection_ids": [9],
                "preview_projection_ids": [7, 8],
                "history_projection_ids": [5, 6],
            },
        },
    )

    # projection.delete the user projection
    write(
        {"type": "update", "fqid": "user/1", "fields": {"projection_$1_ids": [5, 7]}},
        {
            "type": "update",
            "fqid": "projector/2",
            "fields": {"current_projection_ids": []},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"all_projection_ids": [5, 6, 7, 8]},
        },
        {"type": "delete", "fqid": "projection/9"},
    )

    finalize("0037_remove_user_projections")

    # assert that the user projections doesn't exist anymore
    for projection_id in [5, 7, 9]:
        assert_model(f"projection/{projection_id}", DoesNotExist())

    # assert that the user never changes
    for position in range(2, 10):
        assert_model(
            "user/1",
            {
                "username": "test",
                "meta_deleted": False,
                "meta_position": 1,
            },
            position=position,
        )

    # projector.project user
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "meeting/1",
        {
            "motion_ids": [1],
            "projector_ids": [2],
            "all_projection_ids": [],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )

    # projector.project motion
    assert_model(
        "projection/6",
        {
            "meeting_id": 1,
            "current_projector_id": 2,
            "content_object_id": "motion/1",
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [6],
            "history_projection_ids": [],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "meeting/1",
        {
            "motion_ids": [1],
            "projector_ids": [2],
            "all_projection_ids": [6],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "motion/1",
        {
            "meeting_id": 1,
            "projection_ids": [6],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )

    # projector.add_to_preview a user
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [6],
            "preview_projection_ids": [],
            "history_projection_ids": [],
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )
    assert_model(
        "meeting/1",
        {
            "motion_ids": [1],
            "projector_ids": [2],
            "all_projection_ids": [6],
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )

    # projector.next
    assert_model(
        "projection/6",
        {
            "meeting_id": 1,
            "history_projector_id": 2,
            "content_object_id": "motion/1",
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [],
            "preview_projection_ids": [],
            "history_projection_ids": [6],
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "meeting/1",
        {
            "motion_ids": [1],
            "projector_ids": [2],
            "all_projection_ids": [6],
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=5,
    )

    # projector.add_to_preview something else
    assert_model(
        "projection/8",
        {
            "meeting_id": 1,
            "preview_projector_id": 2,
            "content_object_id": "motion/1",
            "meta_deleted": False,
            "meta_position": 6,
        },
        position=6,
    )
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [],
            "history_projection_ids": [6],
            "preview_projection_ids": [8],
            "meta_deleted": False,
            "meta_position": 6,
        },
        position=6,
    )
    assert_model(
        "meeting/1",
        {
            "motion_ids": [1],
            "projector_ids": [2],
            "all_projection_ids": [6, 8],
            "meta_deleted": False,
            "meta_position": 6,
        },
        position=6,
    )
    assert_model(
        "motion/1",
        {
            "meeting_id": 1,
            "projection_ids": [6, 8],
            "meta_deleted": False,
            "meta_position": 6,
        },
        position=6,
    )

    # projector.next: switch to the other projection
    assert_model(
        "projection/8",
        {
            "meeting_id": 1,
            "current_projector_id": 2,
            "content_object_id": "motion/1",
            "meta_deleted": False,
            "meta_position": 7,
        },
        position=7,
    )
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [8],
            "history_projection_ids": [6],
            "preview_projection_ids": [],
            "meta_deleted": False,
            "meta_position": 7,
        },
        position=7,
    )

    # projector.previous
    assert_model(
        "projection/8",
        {
            "meeting_id": 1,
            "preview_projector_id": 2,
            "content_object_id": "motion/1",
            "meta_deleted": False,
            "meta_position": 8,
        },
        position=8,
    )
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [],
            "history_projection_ids": [6],
            "preview_projection_ids": [8],
            "meta_deleted": False,
            "meta_position": 8,
        },
        position=8,
    )

    # projector.previous, again
    assert_model(
        "projection/6",
        {
            "meeting_id": 1,
            "current_projector_id": 2,
            "content_object_id": "motion/1",
            "meta_deleted": False,
            "meta_position": 9,
        },
        position=9,
    )
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [6],
            "history_projection_ids": [],
            "preview_projection_ids": [8],
            "meta_deleted": False,
            "meta_position": 9,
        },
        position=9,
    )

    # projector.add_to_preview a user again
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [6],
            "history_projection_ids": [],
            "preview_projection_ids": [8],
            "meta_deleted": False,
            "meta_position": 10,
        },
        position=10,
    )
    assert_model(
        "meeting/1",
        {
            "motion_ids": [1],
            "projector_ids": [2],
            "all_projection_ids": [6, 8],
            "meta_deleted": False,
            "meta_position": 10,
        },
        position=10,
    )

    # projector.project_preview: specifically project the new user projection
    assert_model(
        "projection/6",
        {
            "meeting_id": 1,
            "history_projector_id": 2,
            "content_object_id": "motion/1",
            "meta_deleted": False,
            "meta_position": 11,
        },
        position=11,
    )
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [],
            "history_projection_ids": [6],
            "preview_projection_ids": [8],
            "meta_deleted": False,
            "meta_position": 11,
        },
        position=11,
    )

    # projection.delete the user projection
    assert_model(
        "projector/2",
        {
            "meeting_id": 1,
            "current_projection_ids": [],
            "history_projection_ids": [6],
            "preview_projection_ids": [8],
            "meta_deleted": False,
            "meta_position": 12,
        },
        position=12,
    )
    assert_model(
        "meeting/1",
        {
            "motion_ids": [1],
            "projector_ids": [2],
            "all_projection_ids": [6, 8],
            "meta_deleted": False,
            "meta_position": 12,
        },
        position=12,
    )


def test_with_meeting(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"all_projection_ids": [1]},
        },
        {
            "type": "create",
            "fqid": "projection/1",
            "fields": {
                "meeting_id": 1,
                "content_object_id": "motion/1",
            },
        },
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {
                "projection_ids": [1],
            },
        },
    )
    finalize("0037_remove_user_projections")

    assert_model(
        "meeting/1",
        {
            "all_projection_ids": [1],
        },
        position=1,
    )
    assert_model(
        "projection/1",
        {
            "meeting_id": 1,
            "content_object_id": "motion/1",
        },
        position=1,
    )
    assert_model(
        "motion/1",
        {
            "projection_ids": [1],
        },
        position=1,
    )
