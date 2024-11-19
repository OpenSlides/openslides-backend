from typing import Any


def create_data() -> dict[str, dict[str, Any]]:
    return {
        "meeting/11": {
            "id": 1,
            "name": "meeting name",
            "present_user_ids": [1, 2],
            "meeting_user_ids": [3],
        },
        "meeting/111": {
            "id": 1,
            "name": "meeting name",
            "present_user_ids": [2],
            "meeting_user_ids": [4],
        },
        "user/1": {
            "id": 1,
            "username": "wrong_user",
            "is_present_in_meeting_ids": [11],
        },
        "user/2": {
            "id": 2,
            "username": "correct_user",
            "is_present_in_meeting_ids": [11, 111],
            "meeting_user_ids": [3, 4],
        },
        "meeting_user/3": {"id": 3, "user_id": 2, "meeting_id": 11},
        "meeting_user/4": {"id": 4, "user_id": 2, "meeting_id": 111},
    }


def test_migration_both_ways(write, finalize, assert_model):
    data = create_data()
    for fqid, fields in data.items():
        write({"type": "create", "fqid": fqid, "fields": fields})

    finalize("0062_unset_presence_of_removed_users")

    data["meeting/11"]["present_user_ids"] = [2]
    data["user/1"]["is_present_in_meeting_ids"] = []

    for fqid, fields in data.items():
        assert_model(fqid, fields)


def test_migration_one_way(write, finalize, assert_model):
    data = create_data()
    data["meeting/11"]["present_user_ids"] = [2]

    for fqid, fields in data.items():
        write({"type": "create", "fqid": fqid, "fields": fields})

    finalize("0062_unset_presence_of_removed_users")

    data["user/1"]["is_present_in_meeting_ids"] = []

    for fqid, fields in data.items():
        assert_model(fqid, fields)


def test_migration_other_way(write, finalize, assert_model):
    data = create_data()
    data["user/1"]["is_present_in_meeting_ids"] = []

    for fqid, fields in data.items():
        write({"type": "create", "fqid": fqid, "fields": fields})

    finalize("0062_unset_presence_of_removed_users")

    data["meeting/11"]["present_user_ids"] = [2]

    for fqid, fields in data.items():
        assert_model(fqid, fields)
