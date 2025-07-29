from collections.abc import Iterable

from .conftest import DoesNotExist


def test_migration(write, finalize, assert_model):
    collection_to_name_key = {
        "user": "username",
        "motion": "title",
        "assignment": "title",
    }

    def write_many(
        create: Iterable[int] = [],
        update: Iterable[int] = [],
        delete: Iterable[int] = [],
        suffix: str = "",
        user_id: int = 1,
    ) -> None:
        actions = {"create": create, "update": update, "delete": delete}
        write(
            *[
                {
                    "type": "create",
                    "fqid": f"{collection}/{id_}",
                    "fields": {
                        "id": id_,
                        namekey: f"{collection}{id_}{suffix}",
                        "meeting_id": 1 if collection != "user" else None,
                    },
                }
                for collection, namekey in collection_to_name_key.items()
                for id_ in create
            ],
            *[
                {
                    "type": "update",
                    "fqid": f"{collection}/{id_}",
                    "fields": {namekey: f"{collection}{id_}{suffix}"},
                }
                for collection, namekey in collection_to_name_key.items()
                for id_ in update
            ],
            *[
                {
                    "type": "delete",
                    "fqid": f"{collection}/{id_}",
                }
                for collection in collection_to_name_key
                for id_ in delete
            ],
            *(
                [
                    {
                        "type": "update",
                        "fqid": "meeting/1",
                        "list_fields": {
                            "add": {"motion_ids": create, "assignment_ids": create},
                            "remove": {"motion_ids": delete, "assignment_ids": delete},
                        },
                    }
                ]
                if create or delete
                else []
            ),
            information={
                f"{collection}/{id_}": [
                    f"{collection.title()} {action}d"
                    for action in ["create", "update", "delete"]
                    if id_ in actions[action]
                ]
                for collection in sorted(collection_to_name_key)
                for id_ in sorted({*create, *update, *delete})
            },
            user_id=user_id,
        )

    write(
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {"id": 1, "username": "admin"},
        },
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"id": 1, "name": "meeting1"},
        },
    )
    write_many(create=[2, 3, 4], suffix="-man")
    write_many(create=[5, 6], update=[3], suffix="-woman", user_id=3)
    write_many(create=[7], update=[4, 5, 6], delete=[5], suffix="-boy")
    write_many(update=[7], delete=[3, 6], suffix="-girl", user_id=2)

    finalize("0068_transfer_history_to_history_collections")

    # First history position is not created because the first position does not have history entries
    assert_model("history_position/1", DoesNotExist())
    assert_model(
        "user/1", {"id": 1, "username": "admin", "history_position_ids": [2, 4]}
    )
    # position_id to collection to model_id to entry_id
    history_entries = {
        2: {
            "assignment": {
                2: 1,
                3: 2,
                4: 3,
            },
            "motion": {
                2: 4,
                3: 5,
                4: 6,
            },
            "user": {
                2: 7,
                3: 8,
                4: 9,
            },
        },
        3: {
            "assignment": {
                3: 10,
                5: 11,
                6: 12,
            },
            "motion": {
                3: 13,
                5: 14,
                6: 15,
            },
            "user": {3: 16, 5: 17, 6: 18},
        },
        4: {
            "assignment": {
                4: 19,
                5: 20,
                6: 21,
                7: 22,
            },
            "motion": {
                4: 23,
                5: 24,
                6: 25,
                7: 26,
            },
            "user": {
                4: 27,
                5: 28,
                6: 29,
                7: 30,
            },
        },
        5: {
            "assignment": {
                3: 31,
                6: 32,
                7: 33,
            },
            "motion": {
                3: 34,
                6: 35,
                7: 36,
            },
            "user": {
                3: 37,
                6: 38,
                7: 39,
            },
        },
    }

    def history_entry_ids(id_: int) -> list[int]:
        return [
            pos[collection][id_]
            for pos in history_entries.values()
            if id_ in pos[collection]
        ]

    for collection, key in collection_to_name_key.items():
        if collection == "user":
            # Only for user 2, because user 3 was deleted already
            add2 = {"history_position_ids": [5]}
            add_other = {}
        else:
            add2 = {}
            add_other = {"meeting_id": 1}
        assert_model(
            f"{collection}/2",
            {
                "id": 2,
                key: f"{collection}2-man",
                "history_entry_ids": history_entry_ids(2),
                **add2,
                **add_other,
            },
        )
        assert_model(
            f"{collection}/3",
            {"id": 3, key: f"{collection}3-woman", "meta_deleted": True, **add_other},
        )
        assert_model(
            f"{collection}/4",
            {
                "id": 4,
                key: f"{collection}4-boy",
                "history_entry_ids": history_entry_ids(4),
                **add_other,
            },
        )
        assert_model(
            f"{collection}/5",
            {"id": 5, key: f"{collection}5-boy", "meta_deleted": True, **add_other},
        )
        assert_model(
            f"{collection}/6",
            {"id": 6, key: f"{collection}6-boy", "meta_deleted": True, **add_other},
        )
        assert_model(
            f"{collection}/7",
            {
                "id": 7,
                key: f"{collection}7-girl",
                "history_entry_ids": history_entry_ids(7),
                **add_other,
            },
        )

    def get_entry_ids_for_position(pos_id: int) -> list[int]:
        return [
            id_
            for connections in history_entries[pos_id].values()
            for id_ in connections.values()
        ]

    assert_model(
        "history_position/2",
        {
            "id": 2,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": get_entry_ids_for_position(2),
        },
        only_check_filled=["timestamp"],
    )
    for collection, connections in history_entries[2].items():
        for id_, entry_id in connections.items():
            fqid = f"{collection}/{id_}"
            data = {
                "id": entry_id,
                "entries": [f"{collection.title()} created"],
                "original_model_id": fqid,
                "position_id": 2,
            }
            if id_ != 3:
                data["model_id"] = fqid
            if collection != "user":
                data["meeting_id"] = 1
            assert_model(
                f"history_entry/{entry_id}",
                data,
            )
    assert_model(
        "history_position/3",
        {"id": 3, "original_user_id": 3, "entry_ids": get_entry_ids_for_position(3)},
        only_check_filled=["timestamp"],
    )
    for collection, connections in history_entries[3].items():
        for id_, entry_id in connections.items():
            if collection != "user":
                add = {"meeting_id": 1}
            else:
                add = {}
            assert_model(
                f"history_entry/{entry_id}",
                {
                    "id": entry_id,
                    "entries": [
                        f"{collection.title()} {'updated' if id_ == 3 else 'created'}"
                    ],
                    "original_model_id": f"{collection}/{id_}",
                    "position_id": 3,
                    **add,
                },
            )
    assert_model(
        "history_position/4",
        {
            "id": 4,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": get_entry_ids_for_position(4),
        },
        only_check_filled=["timestamp"],
    )
    for collection, connections in history_entries[4].items():
        for id_, entry_id in connections.items():
            fqid = f"{collection}/{id_}"
            data = {
                "id": entry_id,
                "original_model_id": fqid,
                "entries": [f"{collection.title()} updated"],
                "position_id": 4,
            }
            if collection != "user":
                data["meeting_id"] = 1
            match id_:
                case 4:
                    data["model_id"] = fqid
                case 5:
                    data["entries"] = [
                        f"{collection.title()} updated",
                        f"{collection.title()} deleted",
                    ]
                case 6:
                    data["entries"] = [f"{collection.title()} updated"]
                case 7:
                    data["model_id"] = fqid
                    data["entries"] = [f"{collection.title()} created"]
            assert_model(
                f"history_entry/{entry_id}",
                data,
            )
    assert_model(
        "history_position/5",
        {
            "id": 5,
            "original_user_id": 2,
            "user_id": 2,
            "entry_ids": get_entry_ids_for_position(5),
        },
        only_check_filled=["timestamp"],
    )
    for collection, connections in history_entries[5].items():
        for id_, entry_id in connections.items():
            fqid = f"{collection}/{id_}"
            data = {
                "id": entry_id,
                "entries": [f"{collection.title()} deleted"],
                "original_model_id": fqid,
                "position_id": 5,
            }
            if collection != "user":
                data["meeting_id"] = 1
            if id_ == 7:
                data["model_id"] = fqid
                data["entries"] = [f"{collection.title()} updated"]
            assert_model(
                f"history_entry/{entry_id}",
                data,
            )
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "meeting1",
            "assignment_ids": [2, 4, 7],
            "motion_ids": [2, 4, 7],
            "relevant_history_entry_ids": [
                id_
                for position in history_entries.values()
                for collection in ["assignment", "motion"]
                for id_ in position[collection].values()
            ],
        },
    )


def test_migration_with_both_history_formats(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {"id": 1, "username": "admin"},
        }
    )
    write(
        {
            "type": "create",
            "fqid": "user/2",
            "fields": {"id": 2, "username": "bob"},
        },
        {
            "type": "create",
            "fqid": "user/3",
            "fields": {"id": 3, "username": "alice"},
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {"id": 2, "name": "bobs club"},
        },
        information=["Users created", "Meeting created"],
    )
    write(
        {
            "type": "update",
            "fqid": "user/2",
            "fields": {"first_name": "bob"},
        },
        {
            "type": "create",
            "fqid": "user/4",
            "fields": {"id": 4, "username": "jeff"},
        },
        {
            "type": "update",
            "fqid": "meeting/2",
            "fields": {"description": "no girls allowed"},
        },
        information={
            "user/2": ["User updated"],
            "user/4": ["User created"],
            "meeting/2": ["Meeting updated"],
        },
    )

    finalize("0068_transfer_history_to_history_collections")

    assert_model(
        "user/1", {"id": 1, "username": "admin", "history_position_ids": [2, 3]}
    )
    assert_model(
        "history_position/2",
        {
            "id": 2,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [1, 2],
        },
        only_check_filled=["timestamp"],
    )
    assert_model(
        "history_entry/1",
        {
            "id": 1,
            "position_id": 2,
            "model_id": "user/2",
            "original_model_id": "user/2",
            "entries": ["Users created", "Meeting created"],
        },
    )
    assert_model(
        "history_entry/2",
        {
            "id": 2,
            "position_id": 2,
            "model_id": "user/3",
            "original_model_id": "user/3",
            "entries": ["Users created", "Meeting created"],
        },
    )
    assert_model(
        "history_position/3",
        {
            "id": 3,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [3, 4],
        },
        only_check_filled=["timestamp"],
    )
    assert_model(
        "history_entry/3",
        {
            "id": 3,
            "position_id": 3,
            "model_id": "user/2",
            "original_model_id": "user/2",
            "entries": ["User updated"],
        },
    )
    assert_model(
        "history_entry/4",
        {
            "id": 4,
            "position_id": 3,
            "model_id": "user/4",
            "original_model_id": "user/4",
            "entries": ["User created"],
        },
    )
    assert_model(
        "user/2",
        {
            "id": 2,
            "username": "bob",
            "first_name": "bob",
            "history_entry_ids": [1, 3],
        },
    )
    assert_model(
        "user/3",
        {
            "id": 3,
            "username": "alice",
            "history_entry_ids": [2],
        },
    )
    assert_model(
        "user/4",
        {
            "id": 4,
            "username": "jeff",
            "history_entry_ids": [4],
        },
    )
    assert_model(
        "meeting/2",
        {
            "id": 2,
            "name": "bobs club",
            "description": "no girls allowed",
        },
    )
    for fqid in ["history_position/4", "history_entry/5"]:
        assert_model(fqid, DoesNotExist())


def test_migration_history_entry_meeting_relation_with_deletions(
    write, finalize, assert_model
):
    write(
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {"id": 1, "username": "admin"},
        },
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"id": 1, "name": "Delete this meeting"},
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {"id": 1, "name": "Keep this meeting"},
        },
    )
    write(
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {"title": "1motion1", "meeting_id": 1},
        },
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {"title": "1motion2", "meeting_id": 1},
        },
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {"title": "2motion1", "meeting_id": 2},
        },
        {
            "type": "create",
            "fqid": "motion/4",
            "fields": {"title": "2motion2", "meeting_id": 2},
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1, 2]},
        },
        {
            "type": "update",
            "fqid": "meeting/2",
            "fields": {"motion_ids": [3, 4]},
        },
        information={
            "motion/1": ["Motion created"],
            "motion/2": ["Motion created"],
            "motion/3": ["Motion created"],
            "motion/4": ["Motion created"],
        },
    )
    write(
        {
            "type": "update",
            "fqid": "motion/1",
            "fields": {"title": "1motion1-edit"},
        },
        {
            "type": "delete",
            "fqid": "motion/2",
        },
        {
            "type": "update",
            "fqid": "motion/3",
            "fields": {"title": "2motion1-edit"},
        },
        {
            "type": "delete",
            "fqid": "motion/4",
        },
        {
            "type": "update",
            "fqid": "meeting/1",
            "fields": {"motion_ids": [1]},
        },
        {
            "type": "update",
            "fqid": "meeting/2",
            "fields": {"motion_ids": [3]},
        },
        information={
            "motion/1": ["Motion updated"],
            "motion/2": ["Motion deleted"],
            "motion/3": ["Motion updated"],
            "motion/4": ["Motion deleted"],
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/1",
        },
        {
            "type": "delete",
            "fqid": "meeting/1",
        },
        information={
            "motion/1": ["Motion deleted"],
        },
    )

    finalize("0068_transfer_history_to_history_collections")

    assert_model(
        "user/1", {"id": 1, "username": "admin", "history_position_ids": [2, 3, 4]}
    )

    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Delete this meeting",
            "motion_ids": [1],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting/2",
        {
            "id": 1,
            "name": "Keep this meeting",
            "motion_ids": [3],
            "relevant_history_entry_ids": [3, 4, 7, 8],
        },
    )

    assert_model(
        "motion/1",
        {
            "title": "1motion1-edit",
            "meeting_id": 1,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion/2",
        {
            "title": "1motion2",
            "meeting_id": 1,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion/3",
        {"title": "2motion1-edit", "meeting_id": 2, "history_entry_ids": [3, 7]},
    )
    assert_model(
        "motion/4",
        {
            "title": "2motion2",
            "meeting_id": 2,
            "meta_deleted": True,
        },
    )

    assert_model(
        "history_position/2",
        {
            "id": 2,
            "user_id": 1,
            "original_user_id": 1,
            "entry_ids": [1, 2, 3, 4],
        },
        only_check_filled=["timestamp"],
    )
    assert_model(
        "history_entry/1",
        {
            "id": 1,
            "original_model_id": "motion/1",
            "position_id": 2,
            "entries": ["Motion created"],
        },
    )
    assert_model(
        "history_entry/2",
        {
            "id": 2,
            "original_model_id": "motion/2",
            "position_id": 2,
            "entries": ["Motion created"],
        },
    )
    assert_model(
        "history_entry/3",
        {
            "id": 3,
            "model_id": "motion/3",
            "original_model_id": "motion/3",
            "position_id": 2,
            "meeting_id": 2,
            "entries": ["Motion created"],
        },
    )
    assert_model(
        "history_entry/4",
        {
            "id": 4,
            "original_model_id": "motion/4",
            "position_id": 2,
            "meeting_id": 2,
            "entries": ["Motion created"],
        },
    )

    assert_model(
        "history_position/3",
        {
            "id": 3,
            "user_id": 1,
            "original_user_id": 1,
            "entry_ids": [5, 6, 7, 8],
        },
        only_check_filled=["timestamp"],
    )
    assert_model(
        "history_entry/5",
        {
            "id": 5,
            "original_model_id": "motion/1",
            "position_id": 3,
            "entries": ["Motion updated"],
        },
    )
    assert_model(
        "history_entry/6",
        {
            "id": 6,
            "original_model_id": "motion/2",
            "position_id": 3,
            "entries": ["Motion deleted"],
        },
    )
    assert_model(
        "history_entry/7",
        {
            "id": 7,
            "model_id": "motion/3",
            "original_model_id": "motion/3",
            "position_id": 3,
            "meeting_id": 2,
            "entries": ["Motion updated"],
        },
    )
    assert_model(
        "history_entry/8",
        {
            "id": 8,
            "original_model_id": "motion/4",
            "position_id": 3,
            "meeting_id": 2,
            "entries": ["Motion deleted"],
        },
    )

    assert_model(
        "history_position/4",
        {
            "id": 4,
            "user_id": 1,
            "original_user_id": 1,
            "entry_ids": [9],
        },
        only_check_filled=["timestamp"],
    )
    assert_model(
        "history_entry/9",
        {
            "id": 9,
            "original_model_id": "motion/1",
            "position_id": 4,
            "entries": ["Motion deleted"],
        },
    )
