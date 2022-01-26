def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 1},
        },
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": [1]},
        },
    )
    write(
        {"type": "delete", "fqid": "meeting/1", "fields": {}},
    )
    write(
        {"type": "restore", "fqid": "meeting/1", "fields": {}},
    )

    finalize("0012_archived_meeting_ids")

    assert_model(
        "organization/1",
        {"meta_deleted": False, "meta_position": 1, "active_meeting_ids": [1]},
        position=1,
    )

    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": True, "meta_position": 2},
        position=2,
    )
    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 3},
        position=3,
    )


def test_one_created_archived_meeting(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 0},
        },
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {},
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "meeting/1",
            "fields": {},
        },
        {
            "type": "restore",
            "fqid": "meeting/1",
            "fields": {},
        },
        {
            "type": "delete",
            "fqid": "meeting/1",
            "fields": {},
        },
    )
    finalize("0012_archived_meeting_ids")
    assert_model(
        "organization/1",
        {"archived_meeting_ids": [1], "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "meeting/1",
        {
            "is_archived_in_organization_id": 1,
            "is_active_in_organization_id": 0,
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        "organization/1",
        {"archived_meeting_ids": [], "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "meeting/1",
        {
            "is_archived_in_organization_id": 1,
            "is_active_in_organization_id": 0,
            "meta_deleted": True,
            "meta_position": 2,
        },
        position=2,
    )


def test_update_meeting(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 1},
        },
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": [1]},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 0},
        },
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": None},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 1},
        },
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": [1]},
        },
    )

    finalize("0012_archived_meeting_ids")

    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "organization/1",
        {"active_meeting_ids": [1], "meta_deleted": False, "meta_position": 1},
        position=1,
    )

    assert_model(
        "meeting/1",
        {
            "is_active_in_organization_id": 0,
            "is_archived_in_organization_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "organization/1",
        {"archived_meeting_ids": [1], "meta_deleted": False, "meta_position": 2},
        position=2,
    )

    assert_model(
        "meeting/1",
        {
            "is_active_in_organization_id": 1,
            "is_archived_in_organization_id": 0,
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "organization/1",
        {
            "active_meeting_ids": [1],
            "archived_meeting_ids": [],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )


def test_create_delete_in_one_position(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {},
        },
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {},
        },
        {
            "type": "delete",
            "fqid": "meeting/1",
            "fields": {},
        },
    )

    finalize("0012_archived_meeting_ids")
    assert_model(
        "organization/1", {"meta_deleted": False, "meta_position": 1}, position=1
    )


def test_single_restore(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 0},
        },
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {},
        },
        {
            "type": "delete",
            "fqid": "meeting/1",
            "fields": {},
        },
    )
    write(
        {
            "type": "restore",
            "fqid": "meeting/1",
            "fields": {},
        }
    )
    finalize("0012_archived_meeting_ids")
    assert_model(
        "organization/1",
        {"archived_meeting_ids": [1], "meta_deleted": False, "meta_position": 2},
        position=2,
    )


def test_update_meeting_2(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 1},
        },
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 0},
        },
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": None},
        },
    )

    finalize("0012_archived_meeting_ids")
    assert_model(
        "organization/1",
        {"archived_meeting_ids": [1], "meta_deleted": False, "meta_position": 1},
        position=1,
    )


def test_update_meeting_3(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 0},
        },
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": []},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 1},
        },
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 0},
        },
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": []},
        },
    )

    finalize("0012_archived_meeting_ids")
    assert_model(
        "organization/1",
        {
            "archived_meeting_ids": [1],
            "active_meeting_ids": [],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )


def test_update_meeting_4(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 0},
        },
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": []},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 1},
        },
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"is_active_in_organization_id": 0},
        },
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"active_meeting_ids": []},
        },
    )
    finalize("0012_archived_meeting_ids")

    assert_model(
        "organization/1",
        {
            "archived_meeting_ids": [1],
            "active_meeting_ids": [],
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
