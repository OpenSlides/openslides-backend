fields = {
    "id": 1,
    "agenda_create": True,
    "agenda_type": "internal",
    "agenda_parent_id": 1,
    "agenda_comment": "comment",
    "agenda_duration": 30,
    "agenda_weight": 42,
}

# Collections which can possibly have agenda items
collections = [
    "assignment",
    "motion",
    "motion_block",
    "topic",
]


def test_migration(write, finalize, assert_model):
    write(
        *[
            {
                "type": "create",
                "fqid": f"{collection}/1",
                "fields": fields,
            }
            for collection in collections
        ]
    )
    write(
        *[
            {
                "type": "update",
                "fqid": f"{collection}/1",
                "fields": fields,
            }
            for collection in collections
        ]
    )
    write(
        *[
            {
                "type": "delete",
                "fqid": f"{collection}/1",
            }
            for collection in collections
        ]
    )
    write(
        *[
            {
                "type": "restore",
                "fqid": f"{collection}/1",
            }
            for collection in collections
        ]
    )

    finalize("0033_remove_agenda_fields_from_other_models")

    for collection in collections:
        assert_model(
            f"{collection}/1",
            {"id": 1, "meta_deleted": False, "meta_position": 1},
            position=1,
        )
        assert_model(
            f"{collection}/1",
            {"id": 1, "meta_deleted": False, "meta_position": 2},
            position=2,
        )
        assert_model(
            f"{collection}/1",
            {"id": 1, "meta_deleted": True, "meta_position": 3},
            position=3,
        )
        assert_model(
            f"{collection}/1",
            {"id": 1, "meta_deleted": False, "meta_position": 4},
            position=4,
        )
