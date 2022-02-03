def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": "meeting/1", "fields": {"id": 1}})
    write(
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"id": 1, "template_meeting_id": 1},
        }
    )

    finalize("0014_rename_template_meeting_id")

    assert_model(
        "committee/1",
        {
            "id": 1,
            "template_meeting_ids": [1],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )


def test_migration_empty_field(write, finalize, assert_model):
    write({"type": "create", "fqid": "meeting/1", "fields": {"id": 1}})
    write(
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"id": 1, "template_meeting_id": None},
        }
    )

    finalize("0014_rename_template_meeting_id")

    assert_model(
        "committee/1",
        {
            "id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
