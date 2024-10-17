from typing import Any

from openslides_backend.shared.patterns import fqid_from_collection_and_id


def generate_agenda_item_data(
    collection: str, base: int, note: str | None
) -> list[dict[str, Any]]:
    co_id = base * 11
    co_fqid = fqid_from_collection_and_id(collection, co_id)
    los_id = base * 111
    return [
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("agenda_item", base),
            "fields": {
                "id": base,
                "content_object_id": co_fqid,
                **({"moderator_notes": note} if note else {}),
            },
        },
        {
            "type": "create",
            "fqid": co_fqid,
            "fields": {
                "id": co_id,
                "agenda_item_id": base,
                "list_of_speakers_id": los_id,
            },
        },
        {
            "type": "create",
            "fqid": fqid_from_collection_and_id("list_of_speakers", los_id),
            "fields": {
                "id": los_id,
                "content_object_id": co_fqid,
            },
        },
    ]


def test_migration_everything(write, finalize, assert_model):
    collection_base_note = [
        ("motion", 1, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("motion", 2, "Hello world!"),
        ("assignment", 3, "Let the election begin"),
        ("topic", 4, "To pick or not to pick a topic"),
        ("motion_block", 5, "A block?"),
        ("topic", 6, None),
    ]
    write(
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "id": 1,
                "permissions": [
                    "agenda_item.can_manage",
                    "agenda_item.can_manage_moderator_notes",
                    "mediafile.can_see",
                ],
            },
        },
        {
            "type": "create",
            "fqid": "group/2",
            "fields": {
                "id": 2,
                "permissions": [
                    "agenda_item.can_see_internal",
                    "agenda_item.can_see_moderator_notes",
                    "motion.can_create",
                ],
            },
        },
        {
            "type": "create",
            "fqid": "group/3",
            "fields": {
                "id": 3,
                "permissions": [
                    "agenda_item.can_manage_moderator_notes",
                    "agenda_item.can_see",
                    "agenda_item.can_see_moderator_notes",
                    "list_of_speakers.can_be_speaker",
                ],
            },
        },
        {
            "type": "create",
            "fqid": "group/4",
            "fields": {
                "id": 4,
                "permissions": [
                    "agenda_item.can_manage_moderator_notes",
                    "list_of_speakers.can_see",
                    "user.can_manage",
                ],
            },
        },
        {
            "type": "create",
            "fqid": "group/5",
            "fields": {
                "id": 5,
                "permissions": [
                    "agenda_item.can_see_internal",
                    "list_of_speakers.can_see",
                ],
            },
        },
        {
            "type": "create",
            "fqid": "group/10",
            "fields": {
                "id": 10,
                "permissions": None,
            },
        },
        *[
            event
            for collection, base, note in collection_base_note
            for event in generate_agenda_item_data(collection, base, note)
        ],
        {
            "type": "create",
            "fqid": "motion/77",
            "fields": {"id": 77, "list_of_speakers_id": 777},
        },
        {
            "type": "create",
            "fqid": "list_of_speakers/777",
            "fields": {
                "id": 777,
                "content_object_id": "motion/77",
            },
        },
    )

    finalize("0060_move_moderator_notes")

    assert_model(
        "group/1",
        {
            "id": 1,
            "permissions": [
                "agenda_item.can_manage",
                "list_of_speakers.can_manage_moderator_notes",
                "mediafile.can_see",
            ],
        },
    )
    assert_model(
        "group/2",
        {
            "id": 2,
            "permissions": [
                "agenda_item.can_see_internal",
                "list_of_speakers.can_see_moderator_notes",
                "motion.can_create",
            ],
        },
    )
    assert_model(
        "group/3",
        {
            "id": 3,
            "permissions": [
                "agenda_item.can_see",
                "list_of_speakers.can_manage_moderator_notes",
                "list_of_speakers.can_see_moderator_notes",
                "list_of_speakers.can_be_speaker",
            ],
        },
    )
    assert_model(
        "group/4",
        {
            "id": 4,
            "permissions": [
                "agenda_item.can_see",
                "list_of_speakers.can_manage_moderator_notes",
                "list_of_speakers.can_see",
                "user.can_manage",
            ],
        },
    )
    assert_model(
        "group/5",
        {
            "id": 5,
            "permissions": [
                "agenda_item.can_see_internal",
                "list_of_speakers.can_see",
            ],
        },
    )
    for collection, base, note in collection_base_note:
        co_fqid = fqid_from_collection_and_id(collection, base * 11)
        assert_model(
            fqid_from_collection_and_id("agenda_item", base),
            {"id": base, "content_object_id": co_fqid},
        )
        expect_los = {
            "id": base * 111,
            "content_object_id": co_fqid,
        }
        if note:
            expect_los["moderator_notes"] = note
        assert_model(
            fqid_from_collection_and_id("list_of_speakers", base * 111),
            expect_los,
        )
    assert_model(
        "list_of_speakers/777",
        {
            "id": 777,
            "content_object_id": "motion/77",
        },
    )


def test_migration_some_collections(write, finalize, assert_model):
    """
    Just to see if leaving some collections out will cause errors
    """
    collection_base_note = [
        ("motion", 1, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("motion", 2, None),
    ]
    write(
        *[
            event
            for collection, base, note in collection_base_note
            for event in generate_agenda_item_data(collection, base, note)
        ],
        {
            "type": "create",
            "fqid": "motion/33",
            "fields": {"id": 33, "list_of_speakers_id": 333},
        },
        {
            "type": "create",
            "fqid": "list_of_speakers/333",
            "fields": {
                "id": 333,
                "content_object_id": "motion/33",
            },
        },
    )

    finalize("0060_move_moderator_notes")

    for collection, base, note in collection_base_note:
        co_fqid = fqid_from_collection_and_id(collection, base * 11)
        assert_model(
            fqid_from_collection_and_id("agenda_item", base),
            {"id": base, "content_object_id": co_fqid},
        )
        expect_los = {
            "id": base * 111,
            "content_object_id": co_fqid,
        }
        if note:
            expect_los["moderator_notes"] = note
        assert_model(
            fqid_from_collection_and_id("list_of_speakers", base * 111),
            expect_los,
        )
    assert_model(
        "list_of_speakers/333",
        {
            "id": 333,
            "content_object_id": "motion/33",
        },
    )
