def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"id": 1, "meeting_mediafile_ids": [1, 2], "group_ids": [1]},
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {
                "id": 2,
                "meeting_mediafile_ids": [3, 4, 6],
                "group_ids": [2, 3],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/1",
            "fields": {"id": 1, "meeting_mediafile_ids": [1, 3]},
        },
        {
            "type": "create",
            "fqid": "mediafile/2",
            "fields": {"id": 2, "meeting_mediafile_ids": [2]},
        },
        {
            "type": "create",
            "fqid": "mediafile/5",
            "fields": {"id": 5, "child_ids": [6], "meeting_mediafile_ids": [4]},
        },
        {
            "type": "create",
            "fqid": "mediafile/6",
            "fields": {"id": 6, "parent_id": 5, "meeting_mediafile_ids": [6]},
        },
        {
            "type": "create",
            "fqid": "meeting_mediafile/1",
            "fields": {
                "id": 1,
                "mediafile_id": 1,
                "meeting_id": 1,
                "access_group_ids": [1],
                "inherited_access_group_ids": [1],
                "is_public": False,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_mediafile/2",
            "fields": {
                "id": 2,
                "mediafile_id": 2,
                "meeting_id": 1,
                "access_group_ids": [1],
                "inherited_access_group_ids": [1],
                "is_public": False,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_mediafile/3",
            "fields": {
                "id": 3,
                "mediafile_id": 1,
                "meeting_id": 2,
                "access_group_ids": [2, 3],
                "inherited_access_group_ids": [2, 3],
                "is_public": False,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_mediafile/4",
            "fields": {
                "id": 4,
                "mediafile_id": 5,
                "meeting_id": 2,
                "access_group_ids": [3],
                "inherited_access_group_ids": [3],
                "is_public": False,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_mediafile/5",
            "fields": {
                "id": 5,
                "mediafile_id": 2,
                "meeting_id": 2,
                "access_group_ids": [4],
                "inherited_access_group_ids": [],
                "is_public": False,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_mediafile/6",
            "fields": {
                "id": 6,
                "mediafile_id": 6,
                "meeting_id": 2,
                "access_group_ids": [2],
                "inherited_access_group_ids": [],
                "is_public": False,
            },
        },
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "id": 1,
                "meeting_id": 1,
                "mediafile_access_group_ids": [1],
                "mediafile_inherited_access_group_ids": [1],
                "meeting_mediafile_access_group_ids": [2],
                "meeting_mediafile_inherited_access_group_ids": [2],
            },
        },
        {
            "type": "create",
            "fqid": "group/2",
            "fields": {
                "id": 2,
                "meeting_id": 2,
                "meeting_mediafile_access_group_ids": [3, 6],
                "meeting_mediafile_inherited_access_group_ids": [3],
            },
        },
        {
            "type": "create",
            "fqid": "group/3",
            "fields": {
                "id": 3,
                "meeting_id": 2,
                "mediafile_access_group_ids": [3, 4],
                "mediafile_inherited_access_group_ids": [3, 4],
            },
        },
        {
            "type": "create",
            "fqid": "group/4",
            "fields": {
                "id": 4,
                "meeting_id": 2,
                "mediafile_id": 2,
                "mediafile_access_group_ids": [5],
                "mediafile_inherited_access_group_ids": [5],
            },
        },
    )
    write(
        {"type": "delete", "fqid": "meeting_mediafile/5", "fields": {}},
        {"type": "delete", "fqid": "group/4", "fields": {}},
    )

    finalize("0056_fix_meeting_mediafile_relations")

    for id_, (meeting_id, access_groups, inherited_access_groups) in {
        1: (1, [1, 2], [1, 2]),
        2: (2, [3, 6], [3]),
        3: (2, [3, 4], [3, 4]),
    }.items():
        assert_model(
            f"group/{id_}",
            {
                "id": id_,
                "meeting_id": meeting_id,
                "meeting_mediafile_access_group_ids": access_groups,
                "meeting_mediafile_inherited_access_group_ids": inherited_access_groups,
            },
        )
