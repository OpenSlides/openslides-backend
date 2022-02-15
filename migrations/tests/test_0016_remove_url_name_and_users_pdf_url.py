def test_migration_users_pdf_url(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"a": 1, "users_pdf_url": False},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"a": 2, "users_pdf_url": True},
        }
    )
    write({"type": "delete", "fqid": "meeting/1"})
    write({"type": "restore", "fqid": "meeting/1"})

    finalize("0016_remove_url_name_and_users_pdf_url")

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


def test_migration_url_name(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"a": 1, "url_name": False},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"a": 2, "url_name": True},
        }
    )
    write({"type": "delete", "fqid": "meeting/1"})
    write({"type": "restore", "fqid": "meeting/1"})
    write({"type": "create", "fqid": "organization/1", "fields": {"a": 1}})
    write({"type": "update", "fqid": "meeting/1", "fields": {"url_name": None}})

    finalize("0016_remove_url_name_and_users_pdf_url")

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
        "organization/1",
        {"a": 1, "meta_deleted": False, "meta_position": 5},
        position=5,
    )
    assert_model(
        "meeting/1",
        {"a": 2, "meta_deleted": False, "meta_position": 6},
        position=6,
    )
