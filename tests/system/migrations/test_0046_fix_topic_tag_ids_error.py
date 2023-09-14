def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "topic/61",
            "fields": {"id": 61, "tag_ids": [], "title": "topic61 with empty tag ids"},
        },
        {
            "type": "create",
            "fqid": "topic/62",
            "fields": {"id": 62, "title": "topic62 without tag ids"},
        },
        {
            "type": "create",
            "fqid": "topic/63",
            "fields": {"id": 63, "tag_ids": [5], "title": "topic63 with tag ids [5]"},
        },
    )
    finalize("0046_fix_topic_tag_ids_error")

    assert_model(
        "topic/61",
        {
            "id": 61,
            "title": "topic61 with empty tag ids",
        },
    )
    assert_model(
        "topic/63",
        {
            "id": 63,
            "title": "topic63 with tag ids [5]",
        },
    )
