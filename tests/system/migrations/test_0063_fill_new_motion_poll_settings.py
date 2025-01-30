def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"id": 1, "name": "Committee 1", "meeting_ids": [1, 2, 3]},
        },
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "id": 1,
                "name": "Meeting 1",
                "committee_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {
                "id": 2,
                "name": "Meeting 2",
                "committee_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "meeting/3",
            "fields": {
                "id": 3,
                "name": "Meeting 3",
                "committee_id": 1,
            },
        },
    )
    write(
        {"type": "delete", "fqid": "meeting/2", "fields": {}},
        {
            "type": "update",
            "fqid": "committee/1",
            "list_fields": {"remove": {"meeting_ids": [2]}},
        },
    )

    finalize("0063_fill_new_motion_poll_settings")

    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Meeting 1",
            "committee_id": 1,
            "motion_poll_projection_name_order_first": "last_name",
            "motion_poll_projection_max_columns": 6,
            "meta_deleted": False,
        },
    )
    assert_model(
        "meeting/2",
        {
            "id": 2,
            "name": "Meeting 2",
            "committee_id": 1,
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting/3",
        {
            "id": 3,
            "name": "Meeting 3",
            "committee_id": 1,
            "motion_poll_projection_name_order_first": "last_name",
            "motion_poll_projection_max_columns": 6,
            "meta_deleted": False,
        },
    )
