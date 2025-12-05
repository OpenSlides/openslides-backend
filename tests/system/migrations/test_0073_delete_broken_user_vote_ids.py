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
        {"type": "create", "fqid": "vote/2", "fields": {"user_id": None}},
        # healthy relation
        {"type": "create", "fqid": "user/3", "fields": {"vote_ids": [4]}},
        {"type": "create", "fqid": "vote/4", "fields": {"user_id": 3}},
        # deleted vote
        {"type": "create", "fqid": "user/5", "fields": {"vote_ids": [6]}},
        {"type": "create", "fqid": "vote/6", "fields": {"user_id": 5}},
        {"type": "delete", "fqid": "vote/6"},
    )

    finalize("0073_delete_broken_user_vote_ids")

    assert_model("user/1", {"vote_ids": []})
    assert_model("vote/2", {})

    assert_model("user/3", {"vote_ids": [4]})
    assert_model("vote/4", {"user_id": 3})

    assert_model("user/5", {"vote_ids": []})
    assert_model("vote/6", {"user_id": 5, "meta_deleted": True})
