from openslides_backend.shared.util import ONE_ORGANIZATION_FQID


def test_migration(write, finalize, assert_model):
    write(
        {"type": "create", "fqid": "meeting/1", "fields": {}},
        {"type": "create", "fqid": ONE_ORGANIZATION_FQID, "fields": {}},
        {"type": "create", "fqid": "meeting/2", "fields": {}},
    )
    write(
        {"type": "create", "fqid": "meeting/3", "fields": {}},
        {"type": "delete", "fqid": "meeting/2", "fields": {}},
    )

    finalize("0002_archive_meetings")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {"active_meeting_ids": [1, 2], "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "meeting/2",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"active_meeting_ids": [1, 3], "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "meeting/2",
        {"is_active_in_organization_id": 1, "meta_deleted": True, "meta_position": 2},
        position=2,
    )
    assert_model(
        "meeting/3",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 2},
        position=2,
    )


def test_no_additional_events(write, finalize, assert_model):
    write({"type": "create", "fqid": ONE_ORGANIZATION_FQID, "fields": {}})

    finalize("0002_archive_meetings")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {"meta_deleted": False, "meta_position": 1},
        position=1,
    )


def test_meeting_after_organization(write, finalize, assert_model):
    write({"type": "create", "fqid": ONE_ORGANIZATION_FQID, "fields": {}})
    write({"type": "create", "fqid": "meeting/1", "fields": {}})

    finalize("0002_archive_meetings")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {"meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"active_meeting_ids": [1], "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 2},
        position=2,
    )


def test_meeting_create_delete(write, finalize, assert_model):
    write({"type": "create", "fqid": ONE_ORGANIZATION_FQID, "fields": {}})
    write(
        {"type": "create", "fqid": "meeting/1", "fields": {}},
        {"type": "delete", "fqid": "meeting/1"},
    )

    finalize("0002_archive_meetings")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {"meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"meta_deleted": False, "meta_position": 1},
        position=2,
    )
    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": True, "meta_position": 2},
        position=2,
    )


def test_meeting_create_delete_restore_one_position(write, finalize, assert_model):
    write({"type": "create", "fqid": ONE_ORGANIZATION_FQID, "fields": {}})
    write(
        {"type": "create", "fqid": "meeting/1", "fields": {}},
        {"type": "delete", "fqid": "meeting/1"},
        {"type": "restore", "fqid": "meeting/1"},
    )

    finalize("0002_archive_meetings")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {"meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"active_meeting_ids": [1], "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 2},
        position=2,
    )


def test_meeting_create_delete_restore_multiple_positions(
    write, finalize, assert_model
):
    write(
        {"type": "create", "fqid": ONE_ORGANIZATION_FQID, "fields": {}},
        {"type": "create", "fqid": "meeting/1", "fields": {}},
    )
    write(
        {"type": "delete", "fqid": "meeting/1"},
        {"type": "restore", "fqid": "meeting/1"},
    )

    finalize("0002_archive_meetings")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {"active_meeting_ids": [1], "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"active_meeting_ids": [1], "meta_deleted": False, "meta_position": 1},
        position=2,
    )
    assert_model(
        "meeting/1",
        {"is_active_in_organization_id": 1, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
