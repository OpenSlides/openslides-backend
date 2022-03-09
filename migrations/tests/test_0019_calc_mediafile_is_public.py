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

    finalize("0019_calc_mediafile_is_public")

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
                "child_ids": [10],
                "is_directory": True,
                "is_public": False,
                "access_group_ids": [1],
                "inherited_access_group_ids": [1],
            },
        },
    )

    finalize("0019_calc_mediafile_is_public")

    assert_model(
        "group/1",
        {
            "id": 1,
            "mediafile_access_group_ids": [11],
            "mediafile_inherited_access_group_ids": [11, 10],
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


def test_migration_varying(write, finalize, assert_model):
    # 1 create directory with access_groups
    write(
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "id": 1,
                "mediafile_access_group_ids": [10],
                "mediafile_inherited_access_group_ids": [10],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/10",
            "fields": {"id": 10, "is_directory": True, "access_group_ids": [1]},
        },
    )

    # 2 create mediafile in directory
    write(
        {
            "type": "create",
            "fqid": "mediafile/11",
            "fields": {"id": 11, "parent_id": 10},
        },
        {
            "type": "update",
            "fqid": "mediafile/10",
            "fields": {"child_ids": [11]},
        },
    )

    # 3 create subdirectory without access_groups and move mediafile to subdirectory
    write(
        {
            "type": "create",
            "fqid": "mediafile/12",
            "fields": {"id": 12, "parent_id": 10, "is_directory": True},
        },
        {
            "type": "update",
            "fqid": "mediafile/10",
            "fields": {"child_ids": [12]},
        },
        {
            "type": "update",
            "fqid": "mediafile/11",
            "fields": {"parent_id": 12},
        },
        {
            "type": "update",
            "fqid": "mediafile/12",
            "fields": {"child_ids": [11]},
        },
    )

    # 4 add group to mediafile, which gives an intersection [] in inherited_access_group_ids
    write(
        {
            "type": "update",
            "fqid": "mediafile/11",
            "list_fields": {
                "add": {"access_group_ids": [2]},
                "remove": {"access_group_ids": []},
            },
        },
    )

    # 5 remove access groups from main-directory and mediafile, all should be public now
    write(
        {
            "type": "update",
            "fqid": "mediafile/11",
            "list_fields": {
                "add": {"access_group_ids": []},
                "remove": {"access_group_ids": [2]},
            },
        },
        {
            "type": "update",
            "fqid": "mediafile/10",
            "list_fields": {
                "remove": {"access_group_ids": [1]},
            },
        },
    )

    finalize("0019_calc_mediafile_is_public")

    # 1 create directory with access_groups
    assert_model(
        "mediafile/10",
        {
            "id": 10,
            "is_public": False,
            "inherited_access_group_ids": [1],
            "access_group_ids": [1],
            "is_directory": True,
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )

    # 2 create mediafile in directory
    assert_model(
        "mediafile/10",
        {
            "id": 10,
            "is_public": False,
            "inherited_access_group_ids": [1],
            "access_group_ids": [1],
            "child_ids": [11],
            "is_directory": True,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "mediafile/11",
        {
            "id": 11,
            "is_public": False,
            "inherited_access_group_ids": [1],
            "parent_id": 10,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )

    # 3 create subdirectory without access_groups and move mediafile to subdirectory
    assert_model(
        "mediafile/10",
        {
            "id": 10,
            "is_public": False,
            "inherited_access_group_ids": [1],
            "access_group_ids": [1],
            "child_ids": [12],
            "is_directory": True,
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "mediafile/11",
        {
            "id": 11,
            "is_public": False,
            "inherited_access_group_ids": [1],
            "parent_id": 12,
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "mediafile/12",
        {
            "id": 12,
            "is_public": False,
            "inherited_access_group_ids": [1],
            "parent_id": 10,
            "child_ids": [11],
            "is_directory": True,
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )

    # 4 add group to mediafile, which gives an intersection [] in inherited_access_group_ids
    assert_model(
        "mediafile/11",
        {
            "id": 11,
            "is_public": False,
            "inherited_access_group_ids": [],
            "access_group_ids": [2],
            "parent_id": 12,
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )

    # 5 remove access groups from main-directory and mediafile, mediafile should be public
    assert_model(
        "mediafile/10",
        {
            "id": 10,
            "is_public": True,
            "inherited_access_group_ids": [],
            "access_group_ids": [],
            "child_ids": [12],
            "is_directory": True,
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "mediafile/11",
        {
            "id": 11,
            "is_public": True,
            "inherited_access_group_ids": [],
            "access_group_ids": [],
            "parent_id": 12,
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "mediafile/12",
        {
            "id": 12,
            "is_public": True,
            "inherited_access_group_ids": [],
            "parent_id": 10,
            "child_ids": [11],
            "is_directory": True,
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )


def test_migration_change_child_thru_parent(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/10",
            "fields": {
                "id": 10,
                "is_directory": True,
                "child_ids": [11],
                "is_public": True,
                "inherited_access_group_ids": [],
                "access_group_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/11",
            "fields": {
                "id": 11,
                "parent_id": 10,
                "is_public": True,
                "inherited_access_group_ids": [],
                "access_group_ids": [],
            },
        },
    )

    write(
        {
            "type": "update",
            "fqid": "mediafile/10",
            "fields": {"access_group_ids": [1], "inherited_access_group_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "group/1",
            "fields": {
                "mediafile_access_group_ids": [10],
                "mediafile_inherited_access_group_ids": [10],
            },
        },
    )

    finalize("0019_calc_mediafile_is_public")

    assert_model(
        "mediafile/10",
        {
            "id": 10,
            "is_public": False,
            "inherited_access_group_ids": [1],
            "access_group_ids": [1],
            "child_ids": [11],
            "is_directory": True,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "mediafile/11",
        {
            "id": 11,
            "is_public": False,
            "inherited_access_group_ids": [1],
            "access_group_ids": [],
            "parent_id": 10,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "group/1",
        {
            "id": 1,
            "mediafile_access_group_ids": [10],
            "mediafile_inherited_access_group_ids": [10, 11],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
