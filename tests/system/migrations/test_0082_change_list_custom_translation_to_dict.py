def test_migration(write, finalize, assert_model):
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    new_ct1: dict[str, str] = {alphabet[i]: alphabet[i + 1] for i in range(0, 26, 2)}
    new_ct2: dict[str, str] = {alphabet[i]: alphabet[-(i + 1)] for i in range(13)}
    old_ct1: list[dict[str, str]] = [
        {"original": original, "translation": translation}
        for original, translation in new_ct1.items()
    ]
    old_ct2: list[dict[str, str]] = [
        {"original": original, "translation": translation}
        for original, translation in new_ct2.items()
    ]
    write(
        *[
            {
                "type": "create",
                "fqid": f"meeting/{i}",
                "fields": {
                    "id": i,
                    "custom_translations": ct,
                },
            }
            for i, ct in enumerate([new_ct1, new_ct2, old_ct1, old_ct2], 1)
        ],
        {
            "type": "create",
            "fqid": "meeting/5",
            "fields": {
                "id": 5,
                "custom_translations": [
                    {"original": "'Tis but a scratch.", "translation": "My arm's off."},
                    {"original": "No it isn't.", "translation": "It definitely is."},
                    {"original": "I've had worse.", "translation": "I'm a liar."},
                    {
                        "original": "Just a flesh wound.",
                        "translation": "Quite a severe injury, actually.",
                    },
                    {"original": "I'm invincible.", "translation": "I'm a loony."},
                    {
                        "original": "The Black Knight always triumphs!",
                        "translation": "The Black Knight is not triumphing this time!",
                    },
                    {
                        "original": "All right, we'll call it a draw.",
                        "translation": "I've lost.",
                    },
                ],
            },
        },
    )
    write(
        {"type": "delete", "fqid": "meeting/1"},
        {"type": "delete", "fqid": "meeting/4"},
    )

    finalize("0082_change_list_custom_translation_to_dict")

    assert_model(
        "meeting/1",
        {
            "id": 1,
            "custom_translations": new_ct1,
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting/2",
        {"id": 2, "custom_translations": new_ct2},
    )
    assert_model(
        "meeting/3",
        {"id": 3, "custom_translations": new_ct1},
    )
    assert_model(
        "meeting/4",
        {
            "id": 4,
            "custom_translations": old_ct2,
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting/5",
        {
            "id": 5,
            "custom_translations": {
                "'Tis but a scratch.": "My arm's off.",
                "No it isn't.": "It definitely is.",
                "I've had worse.": "I'm a liar.",
                "Just a flesh wound.": "Quite a severe injury, actually.",
                "I'm invincible.": "I'm a loony.",
                "The Black Knight always triumphs!": "The Black Knight is not triumphing this time!",
                "All right, we'll call it a draw.": "I've lost.",
            },
        },
    )
