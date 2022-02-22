def test_migration_upload_without_is_public(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "id": 1,
                "mediafile_access_group_ids": [11],
                "mediafile_inherited_access_group_ids": [11],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/11",
            "fields": {
                "id": 11,
                "access_group_ids": [1],
                "inherited_access_group_ids": [1],
            },
        },
    )

    finalize("0018_calc_mediafile_is_public")

    assert_model(
        "group/1",
        {
            "id": 1,
            "mediafile_access_group_ids": [11],
            "mediafile_inherited_access_group_ids": [11],
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        "mediafile/11",
        {
            "id": 11,
            "access_group_ids": [1],
            "inherited_access_group_ids": [1],
            "is_public": False,
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )


def test_migration_upload_with_parent_not_public(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "id": 1,
                "mediafile_access_group_ids": [11],
                "mediafile_inherited_access_group_ids": [11],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/10",
            "fields": {"id": 10, "parent_id": 11, "access_group_ids": []},
        },
        {
            "type": "create",
            "fqid": "mediafile/11",
            "fields": {
                "id": 11,
                "childs": [10],
                "is_directory": True,
                "is_public": False,
                "access_group_ids": [1],
                "inherited_access_group_ids": [1],
            },
        },
    )

    finalize("0018_calc_mediafile_is_public")

    assert_model(
        "group/1",
        {
            "id": 1,
            "mediafile_access_group_ids": [11],
            "mediafile_inherited_access_group_ids": [11],
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        "mediafile/10",
        {
            "id": 10,
            "is_public": False,
            "access_group_ids": [],
            "inherited_access_group_ids": [1],
            "parent_id": 11,
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
