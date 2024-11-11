def test_migration_forwarding_migration(write, finalize, assert_model):
    committee_ids_by_user_id: dict[int, list[int]] = {2: [1, 2, 3], 3: [4], 4: []}
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {
                "id": 1,
                "user_ids": [2, 3, 4, 5],
                "committee_ids": [1, 2, 3, 4, 5],
            },
        },
        *[
            {
                "type": "create",
                "fqid": f"user/{user_id}",
                "fields": {
                    "id": user_id,
                    "organization_id": 1,
                    "forwarding_committee_ids": committee_ids,
                },
            }
            for user_id, committee_ids in committee_ids_by_user_id.items()
        ],
        *[
            {
                "type": "create",
                "fqid": f"committee/{committee_id}",
                "fields": {
                    "id": committee_id,
                    "organization_id": 1,
                    "forwarding_user_id": user_id,
                },
            }
            for user_id, committee_ids in committee_ids_by_user_id.items()
            for committee_id in committee_ids
        ],
        {
            "type": "create",
            "fqid": "user/5",
            "fields": {
                "id": 5,
                "organization_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "committee/5",
            "fields": {
                "id": 5,
                "organization_id": 1,
            },
        },
    )

    finalize("0062_remove_forwarding_user")

    for collection, id_ in [
        *[("user", id_) for id_ in range(2, 6)],
        *[("committee", id_) for id_ in range(1, 6)],
    ]:
        assert_model(
            f"{collection}/{id_}",
            {
                "id": id_,
                "organization_id": 1,
            },
        )
