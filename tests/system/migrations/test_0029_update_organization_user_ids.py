ONE_ORGANIZATION_FQID = "organization/1"
USER_FQID = "user/1"


def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": ONE_ORGANIZATION_FQID,
            "fields": {"id": 1},
        }
    )
    write({"type": "create", "fqid": USER_FQID, "fields": {"id": 1}})
    write({"type": "delete", "fqid": USER_FQID})

    finalize("0029_update_organization_user_ids")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 1,
            "user_ids": [1],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {
            "id": 1,
            "user_ids": [],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        USER_FQID,
        {
            "id": 1,
            "organization_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
