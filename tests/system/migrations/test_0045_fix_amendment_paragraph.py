def test_migration(write, finalize, assert_model, read_model):
    write(
        {
            "type": "create",
            "fqid": "motion/61",
            "fields": {
                "id": 61,
                "amendment_paragraph_$": ["0", "1", "2", "42"],
                "amendment_paragraph_$0": "change",
                "amendment_paragraph_$1": "",
                "amendment_paragraph_$2": "",
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
        {
            "type": "create",
            "fqid": "motion/63",
            "fields": {
                "id": 63,
                "title": "test",
                "amendment_paragraph_$": ["0", "1", "2", "42"],
                "amendment_paragraph_$0": "change",
                "amendment_paragraph_$1": "",
                "amendment_paragraph_$2": "",
                "amendment_paragraph_$42": "change",
            },
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/63",
        }
    )

    finalize("0045_fix_amendment_paragraph")

    assert_model(
        "motion/61",
        {
            "id": 61,
            "amendment_paragraphs": {
                "0": "change",
                "1": "",
                "2": "",
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

    motion63 = read_model("motion/63")
    assert motion63["meta_deleted"] is True
    assert motion63["amendment_paragraph_$"] == ["0", "1", "2", "42"]
