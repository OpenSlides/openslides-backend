def test_migration_simple(write, finalize, assert_model):
    """
    Tests the following cases:
    User pointing to deleted vote gets corrected.
    User and vote intact relation stays untouched.
    User pointing to deleted vote but vote not back gets relation removed entirely.
    """
    write(
        # halfed relation
        {"type": "create", "fqid": "user/1", "fields": {"vote_ids": [2]}},
        {"type": "create", "fqid": "user/2", "fields": {"delegated_vote_ids": [2]}},
        {
            "type": "create",
            "fqid": "vote/2",
            "fields": {"user_id": None, "delegated_user_id": None},
        },
        # healthy relation
        {"type": "create", "fqid": "user/3", "fields": {"vote_ids": [4]}},
        {"type": "create", "fqid": "vote/4", "fields": {"user_id": 3}},
        # deleted vote
        {"type": "create", "fqid": "user/5", "fields": {"vote_ids": [6]}},
        {"type": "create", "fqid": "user/6", "fields": {"delegated_vote_ids": [6]}},
        {
            "type": "create",
            "fqid": "vote/6",
            "fields": {"user_id": 5, "delegated_user_id": 6},
        },
        {"type": "delete", "fqid": "vote/6"},
    )

    finalize("0073_delete_broken_user_vote_ids")

    assert_model("user/1", {"vote_ids": []})
    assert_model("user/2", {"delegated_vote_ids": []})
    assert_model("vote/2", {})

    assert_model("user/3", {"vote_ids": [4]})
    assert_model("vote/4", {"user_id": 3})

    assert_model("user/5", {"vote_ids": []})
    assert_model("user/6", {"delegated_vote_ids": []})
    assert_model("vote/6", {"user_id": 5, "delegated_user_id": 6, "meta_deleted": True})
