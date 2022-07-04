def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"id": 1},
        },
        {
            "type": "create",
            "fqid": "motion_change_recommendation/1",
            "fields": {"id": 1, "line_from": 3, "line_to": 4},
        },
    )

    finalize("0024_decrease_motion_change_recommendation_line_to")

    assert_model(
        "motion_change_recommendation/1",
        {
            "id": 1,
            "line_from": 3,
            "line_to": 3,
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )


def test_migration_mcr_title(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "motion_change_recommendation/1",
            "fields": {"id": 1, "line_from": 0, "line_to": 0},
        }
    )

    finalize("0024_decrease_motion_change_recommendation_line_to")

    assert_model(
        "motion_change_recommendation/1",
        {
            "id": 1,
            "line_from": 0,
            "line_to": 0,
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
