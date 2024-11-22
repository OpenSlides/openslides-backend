from typing import Any


def create_data() -> dict[str, dict[str, Any]]:
    return {
        "meeting/1": {
            "id": 1,
            "name": "meeting name",
            "present_user_ids": [1, 3, 2],
            "meeting_user_ids": [3, 4, 5],
            "group_ids": [10],
        },
        "meeting/2": {
            "id": 1,
            "name": "meeting name",
            "present_user_ids": [2],
            "meeting_user_ids": [6],
        },
        "user/1": {
            "id": 1,
            "username": "correct_user",
            "is_present_in_meeting_ids": [1],
            "meeting_user_ids": [3],
        },
        "user/2": {
            "id": 2,
            "username": "wrong_user",
            "is_present_in_meeting_ids": [2, 1],
            # meeting users do exist after user left meeting but have no group ids
            "meeting_user_ids": [
                5,
                6,
            ],
        },
        "user/3": {
            "id": 3,
            "username": "correct_user",
            "is_present_in_meeting_ids": [1],
            "meeting_user_ids": [4],
        },
        "meeting_user/3": {"id": 3, "user_id": 1, "meeting_id": 1, "group_ids": [10]},
        "meeting_user/4": {"id": 4, "user_id": 3, "meeting_id": 1, "group_ids": [10]},
        "meeting_user/5": {"id": 5, "user_id": 2, "meeting_id": 1, "group_ids": []},
        "meeting_user/6": {"id": 6, "user_id": 2, "meeting_id": 2, "group_ids": []},
        "group/10": {"id": 10, "meeting_user_ids": [3, 4], "meeting_id": 1},
    }


def test_migration_both_ways(write, finalize, assert_model):
    data = create_data()
    for fqid, fields in data.items():
        write({"type": "create", "fqid": fqid, "fields": fields})

    finalize("0062_unset_presence_of_removed_users")

    data["meeting/1"]["present_user_ids"] = [1, 3]
    data["meeting/2"]["present_user_ids"] = []
    data["user/2"]["is_present_in_meeting_ids"] = []

    for fqid, fields in data.items():
        assert_model(fqid, fields)


def test_migration_one_way(write, finalize, assert_model):
    data = create_data()
    data["meeting/1"]["present_user_ids"] = [1, 3]
    data["meeting/2"]["present_user_ids"] = []

    for fqid, fields in data.items():
        write({"type": "create", "fqid": fqid, "fields": fields})

    finalize("0062_unset_presence_of_removed_users")

    data["user/2"]["is_present_in_meeting_ids"] = []

    for fqid, fields in data.items():
        assert_model(fqid, fields)


def test_migration_other_way(write, finalize, assert_model):
    data = create_data()
    data["user/2"]["is_present_in_meeting_ids"] = []

    for fqid, fields in data.items():
        write({"type": "create", "fqid": fqid, "fields": fields})

    finalize("0062_unset_presence_of_removed_users")

    data["meeting/1"]["present_user_ids"] = [1, 3]
    data["meeting/2"]["present_user_ids"] = []

    for fqid, fields in data.items():
        assert_model(fqid, fields)
