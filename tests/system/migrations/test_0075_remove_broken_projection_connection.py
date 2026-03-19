from typing import Any


def test_simple(write, finalize, assert_model):
    test_data: dict[str, dict[str, Any]] = {
        "projection/1": {"content_object_id": None},
        "projection/2": {},
        "meeting/1": {"projection_ids": [1, 2]},
    }

    write(
        *[
            {"type": "create", "fqid": fqid, "fields": data}
            for fqid, data in test_data.items()
        ]
    )

    finalize("0075_remove_broken_projection_connection")

    assert_model(
        "meeting/1",
        {"projection_ids": [1, 2]},
    )
    assert_model(
        "projection/1",
        {"content_object_id": "meeting/1"},
    )
    assert_model(
        "projection/2",
        {"content_object_id": "meeting/1"},
    )


def test_deleted(write, finalize, assert_model):
    test_data: dict[str, dict[str, Any]] = {
        "projection/1": {"content_object_id": None},
        "projection/2": {"content_object_id": "meeting/1"},
        "projection/3": {},
        "meeting/1": {"projection_ids": [1, 2, 3]},
    }

    write(
        *[
            {"type": "create", "fqid": fqid, "fields": data}
            for fqid, data in test_data.items()
        ],
        {"type": "delete", "fqid": "projection/1"},
        {"type": "delete", "fqid": "projection/3"},
    )

    finalize("0075_remove_broken_projection_connection")

    assert_model(
        "meeting/1",
        {"projection_ids": [2]},
    )
    assert_model(
        "projection/1",
        {"meta_deleted": True},
    )
    assert_model(
        "projection/3",
        {"meta_deleted": True},
    )


def test_unrecoverable(write, finalize, assert_model):
    test_data: dict[str, dict[str, Any]] = {
        "projection/1": {"content_object_id": None},
        "projection/2": {},
        "meeting/1": {"projection_ids": []},
    }

    write(
        *[
            {"type": "create", "fqid": fqid, "fields": data}
            for fqid, data in test_data.items()
        ]
    )

    finalize("0075_remove_broken_projection_connection")

    assert_model(
        "meeting/1",
        {"projection_ids": []},
    )
    assert_model(
        "projection/1",
        {"meta_deleted": True},
    )
    assert_model(
        "projection/2",
        {"meta_deleted": True},
    )
