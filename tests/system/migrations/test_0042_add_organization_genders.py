def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": "organization/1", "fields": {"f": 1}})
    write({"type": "create", "fqid": "motion_state/1", "fields": {"f": 1}})
    write({"type": "update", "fqid": "organization/1", "fields": {"f": 2}})
    write({"type": "delete", "fqid": "organization/1"})
    write({"type": "restore", "fqid": "organization/1"})

    finalize("0042_add_organization_genders")

    new_settings = {
        "genders": ["male", "female", "diverse", "non-binary"],
    }

    assert_model(
        "organization/1",
        {
            **new_settings,
            "f": 1,
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        "motion_state/1",
        {"f": 1, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "organization/1",
        {
            **new_settings,
            "f": 2,
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "organization/1",
        {
            **new_settings,
            "f": 2,
            "meta_deleted": True,
            "meta_position": 4,
        },
        position=4,
    )
    assert_model(
        "organization/1",
        {
            **new_settings,
            "f": 2,
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
