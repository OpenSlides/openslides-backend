def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"a": 1, "template_for_committee_id": 1},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"a": 2, "template_for_committee_id": 2},
        }
    )
    write({"type": "delete", "fqid": "meeting/1"})
    write({"type": "restore", "fqid": "meeting/1"})
    write(
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"a": 1, "template_meeting_ids": [1]},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "committee/1",
            "fields": {"a": 2, "template_meeting_ids": [2]},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "committee/1",
            "list_fields": {
                "add": {"template_meeting_ids": [3]},
                "remove": {"template_meeting_ids": [3]},
            },
        }
    )
    write({"type": "delete", "fqid": "committee/1"})
    write({"type": "restore", "fqid": "committee/1"})

    finalize("0018_remove_template_meeting_committee_relation")

    assert_model(
        "meeting/1",
        {"a": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "meeting/1",
        {"a": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "meeting/1",
        {"a": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "meeting/1",
        {"a": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
    assert_model(
        "committee/1",
        {"a": 1, "meta_deleted": False, "meta_position": 5},
        position=5,
    )
    assert_model(
        "committee/1",
        {"a": 2, "meta_deleted": False, "meta_position": 6},
        position=6,
    )
    assert_model(
        "committee/1",
        {"a": 2, "meta_deleted": False, "meta_position": 7},
        position=7,
    )
    assert_model(
        "committee/1",
        {"a": 2, "meta_deleted": True, "meta_position": 8},
        position=8,
    )
    assert_model(
        "committee/1",
        {"a": 2, "meta_deleted": False, "meta_position": 9},
        position=9,
    )
