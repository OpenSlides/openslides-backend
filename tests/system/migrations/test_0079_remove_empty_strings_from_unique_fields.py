from typing import Any


def assert_collection(
    collection_to_field: dict[str, str], write, finalize, assert_model
) -> None:
    test_data: dict[str, dict[str, Any]] = {}
    for collection, field in collection_to_field.items():
        test_data.update(
            {
                f"{collection}/1": {field: "a"},
                f"{collection}/2": {field: ""},
                f"{collection}/3": {},
                f"{collection}/4": {field: ""},
                f"{collection}/5": {field: "e"},
            }
        )
    write(
        *[
            {"type": "create", "fqid": fqid, "fields": data}
            for fqid, data in test_data.items()
        ]
    )
    write(
        *[
            {"type": "delete", "fqid": f"{collection}/4"}
            for collection in collection_to_field
        ]
    )

    finalize("0079_remove_empty_strings_from_unique_fields")

    for collection, field in collection_to_field.items():
        del test_data[f"{collection}/2"][field]
        test_data[f"{collection}/4"]["meta_deleted"] = True

    for fqid, model in test_data.items():
        assert_model(fqid, model)


def test_committee(write, finalize, assert_model):
    assert_collection({"committee": "external_id"}, write, finalize, assert_model)


def test_group(write, finalize, assert_model):
    assert_collection({"group": "external_id"}, write, finalize, assert_model)


def test_meeting(write, finalize, assert_model):
    assert_collection({"meeting": "external_id"}, write, finalize, assert_model)


def test_mediafile(write, finalize, assert_model):
    assert_collection({"mediafile": "title"}, write, finalize, assert_model)


def test_motion(write, finalize, assert_model):
    assert_collection({"motion": "number"}, write, finalize, assert_model)


def test_option(write, finalize, assert_model):
    assert_collection({"option": "text"}, write, finalize, assert_model)


def test_user(write, finalize, assert_model):
    assert_collection({"user": "member_number"}, write, finalize, assert_model)


def test_multi(write, finalize, assert_model):
    assert_collection(
        {
            "committee": "external_id",
            "group": "external_id",
            "meeting": "external_id",
            "mediafile": "title",
            "motion": "number",
            "option": "text",
            "user": "member_number",
        },
        write,
        finalize,
        assert_model,
    )
