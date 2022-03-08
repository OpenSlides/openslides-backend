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
    write(
        {
            "type": "update",
            "fqid": "mediafile/12",
            "fields": {"title": "blablabla"},
        },
    )
    write(
        {
            "type": "create",
            "fqid": "mediafile/13",
            "fields": {"id": 13, "meeting_id": 8},
        },
        {
            "type": "update",
            "fqid": "meeting/8",
            "list_fields": {"add": {"mediafile_ids": [13]}},
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "mediafile/13",
            "fields": {},
        },
        {
            "type": "update",
            "fqid": "meeting/8",
            "list_fields": {"remove": {"mediafile_ids": [13]}},
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "mediafile/12",
            "fields": {},
        },
        {
            "type": "update",
            "fqid": "meeting/8",
            "fields": {"mediafile_ids": None},
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
    assert_model(
        "mediafile/12",
        {
            "id": 12,
            "title": "blablabla",
            "owner_id": "meeting/8",
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "mediafile/13",
        {
            "id": 13,
            "owner_id": "meeting/8",
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "meeting/8",
        {
            "id": 8,
            "mediafile_ids": [12, 13],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "mediafile/13",
        {
            "id": 13,
            "owner_id": "meeting/8",
            "meta_deleted": True,
            "meta_position": 4,
        },
        position=4,
    )
    assert_model(
        "meeting/8",
        {
            "id": 8,
            "mediafile_ids": [12],
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )
    assert_model(
        "mediafile/12",
        {
            "id": 12,
            "title": "blablabla",
            "owner_id": "meeting/8",
            "meta_deleted": True,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "meeting/8",
        {
            "id": 8,
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
