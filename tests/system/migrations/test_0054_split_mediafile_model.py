def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"id": 1, "mediafile_ids": [2, 3]},
        },
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "id": 1,
                "mediafile_ids": [1],
                "group_ids": [1],
                "list_of_speakers_ids": [1],
            },
        },
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {"id": 1, "meeting_id": 1},
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {
                "id": 2,
                "mediafile_ids": [4, 5, 6, 20],
                "group_ids": [2, 3],
                "topic_ids": [1],
                "assignment_ids": [1],
                "motion_ids": [1],
                "all_projection_ids": [1],
            },
        },
        {
            "type": "create",
            "fqid": "group/2",
            "fields": {
                "id": 2,
                "meeting_id": 2,
                "meeting_mediafile_access_group_ids": [4, 6],
                "meeting_mediafile_inherited_access_group_ids": [4, 5, 6],
            },
        },
        {
            "type": "create",
            "fqid": "group/3",
            "fields": {
                "id": 3,
                "meeting_id": 2,
                "meeting_mediafile_access_group_ids": [6],
                "meeting_mediafile_inherited_access_group_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/1",
            "fields": {
                "id": 1,
                "owner_id": "meeting/1",
                "title": "people.csv",
                "filesize": 1234,
                "filename": "people.csv",
                "mimetype": "text/csv",
                "create_timestamp": 1,
                "access_group_ids": [],
                "is_public": True,
                "list_of_speakers_id": 1,
                "inherited_access_group_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "list_of_speakers/1",
            "fields": {"id": 1, "meeting_id": 1, "content_object_id": "mediafile/1"},
        },
        {
            "type": "create",
            "fqid": "mediafile/2",
            "fields": {
                "id": 2,
                "owner_id": "organization/1",
                "title": "Statutes",
                "is_directory": True,
                "create_timestamp": 2,
                "child_ids": [3],
                "is_public": True,
                "inherited_access_group_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/3",
            "fields": {
                "id": 3,
                "owner_id": "organization/1",
                "title": "statutes.pdf",
                "filesize": 2345,
                "filename": "statutes.pdf",
                "mimetype": "application/pdf",
                "pdf_information": {"pages": 2},
                "create_timestamp": 3,
                "token": "a token",
                "parent_id": 2,
                "is_public": False,
                "inherited_access_group_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/4",
            "fields": {
                "id": 4,
                "owner_id": "meeting/2",
                "title": "Presentation",
                "is_directory": True,
                "create_timestamp": 4,
                "child_ids": [5, 6],
                "access_group_ids": [2],
                "inherited_access_group_ids": [2],
                "is_public": False,
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/5",
            "fields": {
                "id": 5,
                "owner_id": "meeting/2",
                "title": "notes.txt",
                "filesize": 3456,
                "filename": "notes.txt",
                "mimetype": "text/plain",
                "create_timestamp": 5,
                "parent_id": 4,
                "inherited_access_group_ids": [2],
                "projection_ids": [1],
                "attachment_ids": ["topic/1"],
                "is_public": False,
            },
        },
        {
            "type": "create",
            "fqid": "projection/1",
            "fields": {"id": 1, "meeting_id": 2, "content_object_id": "mediafile/5"},
        },
        {
            "type": "create",
            "fqid": "mediafile/6",
            "fields": {
                "id": 6,
                "owner_id": "meeting/2",
                "title": "pic.png",
                "filesize": 4567,
                "filename": "pic.png",
                "mimetype": "image/png",
                "create_timestamp": 6,
                "parent_id": 4,
                "access_group_ids": [2, 3],
                "inherited_access_group_ids": [2],
                "attachment_ids": ["topic/1", "motion/1", "assignment/1"],
                "is_public": False,
            },
        },
        {
            "type": "create",
            "fqid": "topic/1",
            "fields": {
                "id": 1,
                "meeting_id": 2,
                "attachment_ids": [5, 6],
            },
        },
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {
                "id": 1,
                "meeting_id": 2,
                "attachment_ids": [6],
            },
        },
        {
            "type": "create",
            "fqid": "assignment/1",
            "fields": {
                "id": 1,
                "meeting_id": 2,
                "attachment_ids": [6],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/20",
            "fields": {
                "id": 20,
                "owner_id": "meeting/2",
                "title": "pic2.png",
                "filesize": 8,
                "filename": "pic2.png",
                "mimetype": "image/png",
                "create_timestamp": 7,
                "access_group_ids": [],
                "inherited_access_group_ids": [],
                "is_public": True,
            },
        },
    )

    finalize("0054_split_mediafile_model")

    assert_model("organization/1", {"id": 1, "mediafile_ids": [2, 3]})
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "mediafile_ids": [1],
            "meeting_mediafile_ids": [1],
            "group_ids": [1],
            "list_of_speakers_ids": [1],
        },
    )
    assert_model(
        "group/1",
        {"id": 1, "meeting_id": 1},
    )
    assert_model(
        "meeting/2",
        {
            "id": 2,
            "mediafile_ids": [4, 5, 6, 20],
            "meeting_mediafile_ids": [4, 5, 6, 20],
            "group_ids": [2, 3],
            "topic_ids": [1],
            "assignment_ids": [1],
            "motion_ids": [1],
            "all_projection_ids": [1],
        },
    )
    assert_model(
        "group/2",
        {
            "id": 2,
            "meeting_id": 2,
            "meeting_mediafile_access_group_ids": [4, 6],
            "meeting_mediafile_inherited_access_group_ids": [4, 5, 6],
        },
    )
    assert_model(
        "group/3",
        {
            "id": 3,
            "meeting_id": 2,
            "meeting_mediafile_access_group_ids": [6],
            "meeting_mediafile_inherited_access_group_ids": [],
        },
    )
    assert_model(
        "mediafile/1",
        {
            "id": 1,
            "owner_id": "meeting/1",
            "title": "people.csv",
            "filesize": 1234,
            "filename": "people.csv",
            "mimetype": "text/csv",
            "create_timestamp": 1,
            "meeting_mediafile_ids": [1],
        },
    )
    assert_model(
        "meeting_mediafile/1",
        {
            "id": 1,
            "mediafile_id": 1,
            "meeting_id": 1,
            "access_group_ids": [],
            "is_public": True,
            "list_of_speakers_id": 1,
            "inherited_access_group_ids": [],
        },
    )
    assert_model(
        "list_of_speakers/1",
        {"id": 1, "meeting_id": 1, "content_object_id": "meeting_mediafile/1"},
    )
    assert_model(
        "mediafile/2",
        {
            "id": 2,
            "owner_id": "organization/1",
            "title": "Statutes",
            "is_directory": True,
            "create_timestamp": 2,
            "child_ids": [3],
        },
    )
    assert_model(
        "mediafile/3",
        {
            "id": 3,
            "owner_id": "organization/1",
            "title": "statutes.pdf",
            "filesize": 2345,
            "filename": "statutes.pdf",
            "mimetype": "application/pdf",
            "pdf_information": {"pages": 2},
            "create_timestamp": 3,
            "token": "a token",
            "parent_id": 2,
        },
    )
    assert_model(
        "mediafile/4",
        {
            "id": 4,
            "owner_id": "meeting/2",
            "title": "Presentation",
            "is_directory": True,
            "create_timestamp": 4,
            "child_ids": [5, 6],
            "meeting_mediafile_ids": [4],
        },
    )
    assert_model(
        "meeting_mediafile/4",
        {
            "id": 4,
            "meeting_id": 2,
            "mediafile_id": 4,
            "access_group_ids": [2],
            "inherited_access_group_ids": [2],
            "is_public": False,
        },
    )
    assert_model(
        "mediafile/5",
        {
            "id": 5,
            "owner_id": "meeting/2",
            "title": "notes.txt",
            "filesize": 3456,
            "filename": "notes.txt",
            "mimetype": "text/plain",
            "create_timestamp": 5,
            "parent_id": 4,
            "meeting_mediafile_ids": [5],
        },
    )
    assert_model(
        "meeting_mediafile/5",
        {
            "id": 5,
            "meeting_id": 2,
            "mediafile_id": 5,
            "inherited_access_group_ids": [2],
            "projection_ids": [1],
            "attachment_ids": ["topic/1"],
            "is_public": False,
        },
    )
    assert_model(
        "projection/1",
        {"id": 1, "meeting_id": 2, "content_object_id": "meeting_mediafile/5"},
    )
    assert_model(
        "mediafile/6",
        {
            "id": 6,
            "owner_id": "meeting/2",
            "title": "pic.png",
            "filesize": 4567,
            "filename": "pic.png",
            "mimetype": "image/png",
            "create_timestamp": 6,
            "parent_id": 4,
            "meeting_mediafile_ids": [6],
        },
    )
    assert_model(
        "meeting_mediafile/6",
        {
            "id": 6,
            "meeting_id": 2,
            "mediafile_id": 6,
            "access_group_ids": [2, 3],
            "inherited_access_group_ids": [2],
            "attachment_ids": ["topic/1", "motion/1", "assignment/1"],
            "is_public": False,
        },
    )
    assert_model(
        "topic/1",
        {
            "id": 1,
            "meeting_id": 2,
            "attachment_meeting_mediafile_ids": [5, 6],
        },
    )
    assert_model(
        "motion/1",
        {"id": 1, "meeting_id": 2, "attachment_meeting_mediafile_ids": [6]},
    )
    assert_model(
        "assignment/1",
        {"id": 1, "meeting_id": 2, "attachment_meeting_mediafile_ids": [6]},
    )
    assert_model(
        "mediafile/20",
        {
            "id": 20,
            "owner_id": "meeting/2",
            "title": "pic2.png",
            "filesize": 8,
            "filename": "pic2.png",
            "mimetype": "image/png",
            "create_timestamp": 7,
            "meeting_mediafile_ids": [20],
        },
    )
    assert_model(
        "meeting_mediafile/20",
        {
            "id": 20,
            "meeting_id": 2,
            "mediafile_id": 20,
            "access_group_ids": [],
            "inherited_access_group_ids": [],
            "is_public": True,
        },
    )
