def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "id": 1,
                "group_ids": [1],
                "meeting_user_ids": [101, 201, 301],
                "motion_submitter_ids": [1011, 1021],
                "personal_note_ids": [1011, 1021],
            },
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {
                "id": 2,
                "group_ids": [2],
                "meeting_user_ids": [102, 202, 302],
                "motion_submitter_ids": [2011, 2012],
                "personal_note_ids": [2021, 2022],
            },
        },
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "id": 1,
                "meeting_id": 1,
                "meeting_user_ids": [101, 301],
            },
        },
        {
            "type": "create",
            "fqid": "group/2",
            "fields": {
                "id": 2,
                "meeting_id": 2,
                "meeting_user_ids": [302],
            },
        },
        {
            "type": "create",
            "fqid": "user/10",
            "fields": {
                "id": 10,
                "meeting_user_ids": [101, 102],
            },
        },
        {
            "type": "create",
            "fqid": "user/20",
            "fields": {
                "id": 20,
                "meeting_user_ids": [201, 202],
            },
        },
        {
            "type": "create",
            "fqid": "user/30",
            "fields": {
                "id": 30,
                "meeting_user_ids": [301, 302],
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/101",
            "fields": {
                "id": 102,
                "meeting_id": 1,
                "group_ids": [1],
                "user_id": 10,
                "assignment_candidate_ids": [1011],
                "chat_message_ids": [1011],
                "motion_submitter_ids": [1011],
                "personal_note_ids": [1011],
                "speaker_ids": [1011],
                "supported_motion_ids": [1],
                "vote_delegations_from_ids": [201, 301],
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/102",
            "fields": {
                "id": 102,
                "meeting_id": 2,
                "group_ids": [],
                "user_id": 10,
                "motion_submitter_ids": [1021],
                "personal_note_ids": [1021],
                "supported_motion_ids": [1, 11],
                "vote_delegations_from_ids": [202, 302],
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/201",
            "fields": {
                "id": 201,
                "meeting_id": 1,
                "group_ids": [],
                "user_id": 20,
                "assignment_candidate_ids": [2011, 2012],
                "chat_message_ids": [2011, 2012],
                "motion_submitter_ids": [2011, 2012],
                "supported_motion_ids": [2, 22],
                "vote_delegated_to_id": 101,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/202",
            "fields": {
                "id": 202,
                "meeting_id": 2,
                "group_ids": [],
                "user_id": 20,
                "personal_note_ids": [2021, 2022],
                "speaker_ids": [2021, 2022],
                "supported_motion_ids": [22],
                "vote_delegated_to_id": 102,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/301",
            "fields": {
                "id": 301,
                "meeting_id": 1,
                "group_ids": [1],
                "user_id": 30,
                "vote_delegated_to_id": 101,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/302",
            "fields": {
                "id": 302,
                "meeting_id": 2,
                "group_ids": [2],
                "user_id": 30,
                "vote_delegated_to_id": 102,
            },
        },
        {
            "type": "create",
            "fqid": "assignment_candidate/1011",
            "fields": {"id": 1011, "meeting_user_id": 101},
        },
        {
            "type": "create",
            "fqid": "assignment_candidate/2011",
            "fields": {"id": 2011, "meeting_user_id": 201},
        },
        {
            "type": "create",
            "fqid": "assignment_candidate/2012",
            "fields": {"id": 2012, "meeting_user_id": 201},
        },
        {
            "type": "create",
            "fqid": "chat_message/1011",
            "fields": {"id": 1011, "meeting_user_id": 101},
        },
        {
            "type": "create",
            "fqid": "chat_message/2011",
            "fields": {"id": 2011, "meeting_user_id": 201},
        },
        {
            "type": "create",
            "fqid": "chat_message/2012",
            "fields": {"id": 2012, "meeting_user_id": 201},
        },
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {
                "id": 1,
                "submitter_ids": [1011, 1021],
                "personal_note_ids": [1011, 1021],
                "supporter_meeting_user_ids": [101, 102],
            },
        },
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {
                "id": 2,
                "submitter_ids": [2011, 2012],
                "personal_note_ids": [2021, 2022],
                "supporter_meeting_user_ids": [201],
            },
        },
        {
            "type": "create",
            "fqid": "motion/11",
            "fields": {
                "id": 11,
                "supporter_meeting_user_ids": [102],
            },
        },
        {
            "type": "create",
            "fqid": "motion/22",
            "fields": {
                "id": 22,
                "supporter_meeting_user_ids": [201, 202],
            },
        },
        {
            "type": "create",
            "fqid": "motion_submitter/1011",
            "fields": {
                "id": 1011,
                "meeting_user_id": 101,
                "meeting_id": 1,
                "motion_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "motion_submitter/1021",
            "fields": {
                "id": 1021,
                "meeting_user_id": 102,
                "meeting_id": 1,
                "motion_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "motion_submitter/2011",
            "fields": {
                "id": 2011,
                "meeting_user_id": 201,
                "meeting_id": 2,
                "motion_id": 2,
            },
        },
        {
            "type": "create",
            "fqid": "motion_submitter/2012",
            "fields": {
                "id": 2012,
                "meeting_user_id": 201,
                "meeting_id": 2,
                "motion_id": 2,
            },
        },
        {
            "type": "create",
            "fqid": "personal_note/1011",
            "fields": {
                "id": 1011,
                "meeting_user_id": 101,
                "meeting_id": 1,
                "content_object_id": "motion/1",
            },
        },
        {
            "type": "create",
            "fqid": "personal_note/1021",
            "fields": {
                "id": 1021,
                "meeting_user_id": 102,
                "meeting_id": 1,
                "content_object_id": "motion/1",
            },
        },
        {
            "type": "create",
            "fqid": "personal_note/2021",
            "fields": {
                "id": 2021,
                "meeting_user_id": 202,
                "meeting_id": 2,
                "content_object_id": "motion/2",
            },
        },
        {
            "type": "create",
            "fqid": "personal_note/2022",
            "fields": {
                "id": 2022,
                "meeting_user_id": 202,
                "meeting_id": 2,
                "content_object_id": "motion/2",
            },
        },
        {
            "type": "create",
            "fqid": "speaker/1011",
            "fields": {
                "id": 1011,
                "meeting_user_id": 101,
            },
        },
        {
            "type": "create",
            "fqid": "speaker/2021",
            "fields": {
                "id": 2021,
                "meeting_user_id": 202,
            },
        },
        {
            "type": "create",
            "fqid": "speaker/2022",
            "fields": {
                "id": 2022,
                "meeting_user_id": 202,
            },
        },
    )

    finalize("0049_delete_removed_meeting_users")

    assert_model(
        "meeting_user/102",
        {
            "id": 102,
            "meeting_id": 2,
            "group_ids": [],
            "user_id": 10,
            "motion_submitter_ids": [1021],
            "personal_note_ids": [1021],
            "supported_motion_ids": [1, 11],
            "vote_delegations_from_ids": [202, 302],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/201",
        {
            "id": 201,
            "meeting_id": 1,
            "group_ids": [],
            "user_id": 20,
            "assignment_candidate_ids": [2011, 2012],
            "chat_message_ids": [2011, 2012],
            "motion_submitter_ids": [2011, 2012],
            "supported_motion_ids": [2, 22],
            "vote_delegated_to_id": 101,
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/202",
        {
            "id": 202,
            "meeting_id": 2,
            "group_ids": [],
            "user_id": 20,
            "personal_note_ids": [2021, 2022],
            "speaker_ids": [2021, 2022],
            "supported_motion_ids": [22],
            "meta_deleted": True,
            "vote_delegated_to_id": 102,
        },
    )

    assert_model(
        "meeting_user/101",
        {
            "id": 102,
            "meeting_id": 1,
            "group_ids": [1],
            "user_id": 10,
            "assignment_candidate_ids": [1011],
            "chat_message_ids": [1011],
            "motion_submitter_ids": [1011],
            "personal_note_ids": [1011],
            "speaker_ids": [1011],
            "supported_motion_ids": [1],
            "vote_delegations_from_ids": [301],
        },
    )
    assert_model(
        "meeting_user/301",
        {
            "id": 301,
            "meeting_id": 1,
            "group_ids": [1],
            "user_id": 30,
            "vote_delegated_to_id": 101,
        },
    )
    assert_model(
        "meeting_user/302",
        {
            "id": 302,
            "meeting_id": 2,
            "group_ids": [2],
            "user_id": 30,
        },
    )
    assert_model("assignment_candidate/1011", {"id": 1011, "meeting_user_id": 101})
    assert_model(
        "assignment_candidate/2011",
        {
            "id": 2011,
        },
    )
    assert_model(
        "assignment_candidate/2012",
        {
            "id": 2012,
        },
    )
    assert_model("chat_message/1011", {"id": 1011, "meeting_user_id": 101})
    assert_model(
        "chat_message/2011",
        {
            "id": 2011,
        },
    )
    assert_model(
        "chat_message/2012",
        {
            "id": 2012,
        },
    )
    assert_model(
        "motion_submitter/1011",
        {
            "id": 1011,
            "meeting_user_id": 101,
            "meeting_id": 1,
            "motion_id": 1,
        },
    )
    assert_model(
        "motion_submitter/1021",
        {
            "id": 1021,
            "meeting_user_id": 102,
            "meeting_id": 1,
            "motion_id": 1,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_submitter/2011",
        {
            "id": 2011,
            "meeting_user_id": 201,
            "meeting_id": 2,
            "motion_id": 2,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_submitter/2012",
        {
            "id": 2012,
            "meeting_user_id": 201,
            "meeting_id": 2,
            "motion_id": 2,
            "meta_deleted": True,
        },
    )
    assert_model(
        "personal_note/1011",
        {
            "id": 1011,
            "meeting_user_id": 101,
            "meeting_id": 1,
            "content_object_id": "motion/1",
        },
    )
    assert_model(
        "personal_note/1021",
        {
            "id": 1021,
            "meeting_user_id": 102,
            "meeting_id": 1,
            "content_object_id": "motion/1",
            "meta_deleted": True,
        },
    )
    assert_model(
        "personal_note/2021",
        {
            "id": 2021,
            "meeting_user_id": 202,
            "meeting_id": 2,
            "content_object_id": "motion/2",
            "meta_deleted": True,
        },
    )
    assert_model(
        "personal_note/2022",
        {
            "id": 2022,
            "meeting_user_id": 202,
            "meeting_id": 2,
            "content_object_id": "motion/2",
            "meta_deleted": True,
        },
    )
    assert_model(
        "speaker/1011",
        {
            "id": 1011,
            "meeting_user_id": 101,
        },
    )
    assert_model(
        "speaker/2021",
        {
            "id": 2021,
        },
    )
    assert_model(
        "speaker/2022",
        {
            "id": 2022,
        },
    )
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "group_ids": [1],
            "meeting_user_ids": [101, 301],
            "motion_submitter_ids": [1011],
            "personal_note_ids": [1011],
        },
    )
    assert_model(
        "meeting/2",
        {
            "id": 2,
            "group_ids": [2],
            "meeting_user_ids": [302],
            "motion_submitter_ids": [],
            "personal_note_ids": [],
        },
    )
    assert_model(
        "motion/1",
        {
            "id": 1,
            "submitter_ids": [1011],
            "personal_note_ids": [1011],
            "supporter_meeting_user_ids": [101],
        },
    )
    assert_model(
        "motion/2",
        {
            "id": 2,
            "submitter_ids": [],
            "personal_note_ids": [],
            "supporter_meeting_user_ids": [],
        },
    )
    assert_model(
        "motion/11",
        {
            "id": 11,
            "supporter_meeting_user_ids": [],
        },
    )
    assert_model(
        "motion/22",
        {
            "id": 22,
            "supporter_meeting_user_ids": [],
        },
    )
    assert_model(
        "group/1",
        {
            "id": 1,
            "meeting_id": 1,
            "meeting_user_ids": [101, 301],
        },
    )
    assert_model(
        "group/2",
        {
            "id": 2,
            "meeting_id": 2,
            "meeting_user_ids": [302],
        },
    )
    assert_model(
        "user/10",
        {
            "id": 10,
            "meeting_user_ids": [101],
        },
    )
    assert_model(
        "user/20",
        {
            "id": 20,
            "meeting_user_ids": [],
        },
    )
    assert_model(
        "user/30",
        {
            "id": 30,
            "meeting_user_ids": [301, 302],
        },
    )
