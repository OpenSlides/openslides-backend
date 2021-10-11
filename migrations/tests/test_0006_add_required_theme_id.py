def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"id": 42},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "organization/1",
            "fields": {"f": 2},
        }
    )
    write({"type": "delete", "fqid": "organization/1"})
    write({"type": "restore", "fqid": "organization/1"})

    finalize("0006_add_required_theme_id")

    assert_model(
        "organization/1",
        {"id": 42, "theme_id": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        "theme/1",
        {
            "id": 1,
            "name": "OpenSlides Blue",
            "accent_500": "#2196f3",
            "primary_500": "#317796",
            "warn_500": "#f06400",
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        "organization/1",
        {"id": 42, "f": 2, "theme_id": 1, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "organization/1",
        {"id": 42, "f": 2, "theme_id": 1, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        "organization/1",
        {"id": 42, "f": 2, "theme_id": 1, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
