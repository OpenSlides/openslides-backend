def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "motion/61",
            "fields": {
                "id": 61,
                "amendment_paragraph_$": ["0", "1", "2", "42"],
                "amendment_paragraph_$0": "change",
                "amendment_paragraph_$1": "change",
                "amendment_paragraph_$2": "change",
                "amendment_paragraph_$42": "change",
            },
        },
        {
            "type": "create",
            "fqid": "motion/62",
            "fields": {
                "id": 62,
                "title": "test",
            },
        },
    )
    finalize("0045_fix_amendment_paragraph")

    assert_model(
        "motion/61",
        {
            "id": 61,
            "amendment_paragraphs": {
                "0": "change",
                "1": "change",
                "2": "change",
                "42": "change",
            },
        },
    )
    assert_model(
        "motion/62",
        {
            "id": 62,
            "title": "test",
        },
    )
