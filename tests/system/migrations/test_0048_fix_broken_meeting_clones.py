def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {
                "id": 1,
                "archived_meeting_ids": [101],
                "active_meeting_ids": [100, 102],
                "committee_ids": [10],
            },
        },
        {
            "type": "create",
            "fqid": "committee/10",
            "fields": {
                "id": 10,
                "organization_id": 1,
                "meeting_ids": [100, 101, 102, 103],
            },
        },
        {
            "type": "create",
            "fqid": "meeting/100",
            "fields": {
                "id": 100,
                "name": "Active",
                "committee_id": 10,
                "is_active_in_organization_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "meeting/101",
            "fields": {
                "id": 101,
                "name": "Archived",
                "committee_id": 10,
                "is_archived_in_organization_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "meeting/102",
            "fields": {
                "id": 102,
                "name": "Copy of archived",
                "committee_id": 10,
                "is_active_in_organization_id": 1,
                "is_archived_in_organization_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "meeting/103",
            "fields": {
                "id": 103,
                "name": "Archived copy of archived",
                "committee_id": 10,
                "is_archived_in_organization_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "meeting/104",
            "fields": {
                "id": 104,
                "name": "Archived copy of archived2",
                "committee_id": 10,
                "is_archived_in_organization_id": 1,
            },
        },
    )
    write({"type": "delete", "fqid": "meeting/104"})

    finalize("0048_fix_broken_meeting_clones")

    assert_model(
        "organization/1",
        {
            "id": 1,
            "committee_ids": [10],
            "active_meeting_ids": [100, 102],
            "archived_meeting_ids": [101, 103],
        },
    )
    assert_model(
        "meeting/100",
        {
            "id": 100,
            "name": "Active",
            "committee_id": 10,
            "is_active_in_organization_id": 1,
        },
    )
    assert_model(
        "meeting/101",
        {
            "id": 101,
            "name": "Archived",
            "committee_id": 10,
            "is_archived_in_organization_id": 1,
        },
    )
    assert_model(
        "meeting/102",
        {
            "id": 102,
            "name": "Copy of archived",
            "committee_id": 10,
            "is_active_in_organization_id": 1,
        },
    )
    assert_model(
        "meeting/103",
        {
            "id": 103,
            "name": "Archived copy of archived",
            "committee_id": 10,
            "is_archived_in_organization_id": 1,
        },
    )
    assert_model(
        "meeting/104",
        {
            "id": 104,
            "name": "Archived copy of archived2",
            "committee_id": 10,
            "is_archived_in_organization_id": 1,
            "meta_deleted": True,
        },
    )
