def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "topic/61",
            "fields": {
                "id": 61,
                "tag_ids": [],
                "title": "topic61 with empty tag ids"
            },
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
