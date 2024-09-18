def create_data(write):
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"id": 1, "genders": ["male", "female", "diverse", "non-binary"]},
        },
        {"type": "create", "fqid": "user/1", "fields": {"id": 1, "gender": "male"}},
        {"type": "create", "fqid": "user/2", "fields": {"id": 2, "gender": "female"}},
        {"type": "create", "fqid": "user/3", "fields": {"id": 3, "gender": "diverse"}},
        {
            "type": "create",
            "fqid": "user/4",
            "fields": {"id": 4, "gender": "non-binary"},
        },
        {
            "type": "create",
            "fqid": "user/5",
            "fields": {"id": 5, "gender": "non-binary"},
        },
    )


def test_migration_full(write, finalize, assert_model):
    create_data(write)

    finalize("0056_gender_model")

    assert_model(
        "gender/3",
        {"id": 3, "name": "diverse", "organization_id": 1, "user_ids": [3]},
    )
    assert_model(
        "gender/4",
        {"id": 4, "name": "non-binary", "organization_id": 1, "user_ids": [4, 5]},
    )
    assert_model(
        "user/5",
        {
            "id": 5,
            "gender_id": 4,
        },
    )


def test_migration_with_empty_gender(write, finalize, assert_model):
    create_data(write)
    write(
        {"type": "create", "fqid": "user/6", "fields": {"id": 6, "gender": None}},
    )

    finalize("0056_gender_model")

    assert_model(
        "gender/4",
        {"id": 4, "name": "non-binary", "organization_id": 1, "user_ids": [4, 5]},
    )
    assert_model(
        "user/6",
        {
            "id": 6,
        },
    )
