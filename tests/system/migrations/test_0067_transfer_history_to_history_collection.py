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
                    "fields": {"id": id_, namekey: f"{collection}{id_}{suffix}"},
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
        }
    )
    write_many(create=[2, 3, 4], suffix="-man")
    write_many(create=[5, 6], update=[3], suffix="-woman", user_id=3)
    write_many(create=[7], update=[4, 5, 6], delete=[5], suffix="-boy")
    write_many(update=[7], delete=[3, 6], suffix="-girl", user_id=2)

    finalize("0067_transfer_history_to_history_collections")

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
        else:
            add2 = {}
        assert_model(
            f"{collection}/2",
            {
                "id": 2,
                key: f"{collection}2-man",
                "history_entry_ids": history_entry_ids(2),
                **add2,
            },
        )
        assert_model(
            f"{collection}/3",
            {
                "id": 3,
                key: f"{collection}3-woman",
                "meta_deleted": True,
            },
        )
        assert_model(
            f"{collection}/4",
            {
                "id": 4,
                key: f"{collection}4-boy",
                "history_entry_ids": history_entry_ids(4),
            },
        )
        assert_model(
            f"{collection}/5",
            {"id": 5, key: f"{collection}5-boy", "meta_deleted": True},
        )
        assert_model(
            f"{collection}/6",
            {"id": 6, key: f"{collection}6-boy", "meta_deleted": True},
        )
        assert_model(
            f"{collection}/7",
            {
                "id": 7,
                key: f"{collection}7-girl",
                "history_entry_ids": history_entry_ids(7),
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
            assert_model(
                f"history_entry/{entry_id}",
                {
                    "id": entry_id,
                    "entries": [
                        f"{collection.title()} {'updated' if id_ == 3 else 'created'}"
                    ],
                    "original_model_id": f"{collection}/{id_}",
                    "position_id": 3,
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
            if id_ == 7:
                data["model_id"] = fqid
                data["entries"] = [f"{collection.title()} updated"]
            assert_model(
                f"history_entry/{entry_id}",
                data,
            )
