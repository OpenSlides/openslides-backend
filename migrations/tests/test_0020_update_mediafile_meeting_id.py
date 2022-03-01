def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/8",
            "fields": {"id": 8, "mediafile_ids": [12]},
        },
        {
            "type": "create",
            "fqid": "mediafile/12",
            "fields": {"id": 12, "meeting_id": 8},
        },
    )

    finalize("0020_update_mediafile_meeting_id")

    assert_model(
        "meeting/8",
        {
            "id": 8,
            "mediafile_ids": [12],
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        "mediafile/12",
        {
            "id": 12,
            "owner_id": "meeting/8",
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
