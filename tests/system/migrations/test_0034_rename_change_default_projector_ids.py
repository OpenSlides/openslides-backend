def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "id": 1,
                "default_projector_$_id": ["topics"],
                "default_projector_$topics_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projector/11",
            "fields": {
                "id": 11,
                "used_as_default_$_in_meeting_id": ["topics"],
                "used_as_default_$topics_in_meeting_id": 1,
            },
        },
    )
    finalize("0034_rename_change_default_projector_ids")
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "default_projector_$_ids": ["topics"],
            "default_projector_$topics_ids": [11],
            "meta_deleted": False,
            "meta_position": 1,
        },
    )


def test_migration_delete_list(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "id": 1,
                "default_projector_$_id": ["topics"],
                "default_projector_$topics_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projector/11",
            "fields": {
                "id": 11,
                "used_as_default_$_in_meeting_id": ["topics"],
                "used_as_default_$topics_in_meeting_id": 1,
            },
        },
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {
                "default_projector_$_id": None,
                "default_projector_$topics_id": None,
            },
        },
        {
            "type": "update",
            "fqid": "projector/11",
            "fields": {
                "used_as_default_$_in_meeting_id": None,
                "used_as_default_$topics_in_meeting_id": None,
            },
        },
    )
    finalize("0034_rename_change_default_projector_ids")
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
    )
