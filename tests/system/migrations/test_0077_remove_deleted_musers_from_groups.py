def test_simple(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {"meeting_user_ids": [1, 2, 3, 6]},
        },
        {"type": "create", "fqid": "group/2", "fields": {"meeting_user_ids": [2, 4]}},
        {"type": "create", "fqid": "group/3", "fields": {"meeting_user_ids": [5]}},
        {"type": "create", "fqid": "group/4", "fields": {"meeting_user_ids": [1, 3]}},
        {"type": "create", "fqid": "meeting_user/1", "fields": {"group_ids": [1, 4]}},
        {"type": "create", "fqid": "meeting_user/2", "fields": {"group_ids": [1, 2]}},
        {"type": "create", "fqid": "meeting_user/4", "fields": {"group_ids": [2]}},
        {"type": "create", "fqid": "meeting_user/5", "fields": {"group_ids": [3]}},
        {"type": "create", "fqid": "meeting_user/6", "fields": {"group_ids": []}},
    )
    write(
        {"type": "delete", "fqid": "group/3"},
        {"type": "delete", "fqid": "meeting_user/2"},
        {"type": "delete", "fqid": "meeting_user/5"},
        {"type": "delete", "fqid": "meeting_user/6"},
    )

    finalize("0077_remove_deleted_musers_from_groups")

    assert_model("group/1", {"meeting_user_ids": [1]})
    assert_model("group/2", {"meeting_user_ids": [4]})
    assert_model("group/4", {"meeting_user_ids": [1]})
