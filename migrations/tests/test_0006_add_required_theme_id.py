ONE_ORGANIZATION_FQID = "organization/1"


def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": ONE_ORGANIZATION_FQID,
            "fields": {"id": 42},
        }
    )
    write(
        {
            "type": "update",
            "fqid": ONE_ORGANIZATION_FQID,
            "fields": {"f": 2},
        }
    )
    write({"type": "delete", "fqid": ONE_ORGANIZATION_FQID})
    write({"type": "restore", "fqid": ONE_ORGANIZATION_FQID})
    write({"type": "create", "fqid": "dummy/42", "fields": {"id": 42}})

    finalize("0006_add_required_theme_id")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 42,
            "theme_id": 1,
            "theme_ids": [1],
            "meta_deleted": False,
            "meta_position": 1,
        },
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
            "organization_id": 1,
            "theme_for_organization_id": 1,
        },
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 42,
            "f": 2,
            "theme_id": 1,
            "theme_ids": [1],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 42,
            "f": 2,
            "theme_id": 1,
            "theme_ids": [1],
            "meta_deleted": True,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 42,
            "f": 2,
            "theme_id": 1,
            "theme_ids": [1],
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )
    assert_model(
        "dummy/42",
        {
            "id": 42,
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
