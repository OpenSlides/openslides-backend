from typing import Any


def test_simple(write, finalize, assert_model):
    test_data: dict[str, dict[str, Any]] = {
        "projection/1": {"content_object_id": None},
        "meeting/1": {"projection_ids": [1]},
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
        {"projection_ids": [1]},
    )
    assert_model(
        "projection/1",
        {"content_object_id": "meeting/1"},
    )


def test_unrecoverable(write, finalize, assert_model):
    test_data: dict[str, dict[str, Any]] = {
        "projection/1": {"content_object_id": None},
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
