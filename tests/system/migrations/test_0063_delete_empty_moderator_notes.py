from typing import Any

from openslides_backend.shared.patterns import fqid_from_collection_and_id


def generate_agenda_item_data(
    collection: str, base: int, note: str | None
) -> list[dict[str, Any]]:
    co_id = base * 11
    co_fqid = fqid_from_collection_and_id(collection, co_id)
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
            },
        },
    ]


def test_migration_everything(write, finalize, assert_model):
    collection_base_note = [
        ("motion", 1, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("motion", 2, ""),
        ("assignment", 3, ""),
        ("topic", 4, ""),
        ("motion_block", 5, ""),
        ("topic", 6, None),
    ]
    write(
        *[
            event
            for collection, base, note in collection_base_note
            for event in generate_agenda_item_data(collection, base, note)
        ],
    )

    finalize("0063_delete_empty_moderator_notes")

    for collection, base, note in collection_base_note:
        co_fqid = fqid_from_collection_and_id(collection, base * 11)
        assert_model(
            fqid_from_collection_and_id("agenda_item", base),
            {"id": base, "content_object_id": co_fqid},
        )
