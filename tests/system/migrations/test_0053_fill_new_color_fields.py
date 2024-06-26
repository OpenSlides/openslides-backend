projector_events = [
    {
        "type": "create",
        "fqid": "projector/3",
        "fields": {
            "id": 3,
            "chyron_background_color": "#c8dcf0",  # (200, 220, 240) -> (156, 189, 225) -> (167, 196, 228) -> #a7c4e4
            "chyron_font_color": "#ffffff",
        },
    },
    {
        "type": "create",
        "fqid": "projector/4",
        "fields": {"id": 4, "chyron_font_color": "#000000"},
    },
    {
        "type": "create",
        "fqid": "projector/5",
        "fields": {
            "id": 5,
        },
    },
]


def test_migration_with_empty_theme(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"id": 1, "theme_id": 2, "theme_ids": [2]},
        },
        {
            "type": "create",
            "fqid": "theme/2",
            "fields": {
                "id": 2,
                "organization_id": 1,
                "theme_for_organization_id": 1,
            },
        },
        *projector_events
    )

    finalize("0053_fill_new_color_fields")

    assert_model(
        "projector/3",
        {
            "id": 3,
            "chyron_background_color": "#c8dcf0",
            "chyron_font_color": "#ffffff",
            "chyron_background_color_2": "#a7c4e4",
            "chyron_font_color_2": "#ffffff",
        },
    )
    assert_model(
        "projector/4",
        {
            "id": 4,
            "chyron_font_color": "#000000",
            "chyron_background_color_2": "#134768",
            "chyron_font_color_2": "#000000",
        },
    )
    assert_model(
        "projector/5",
        {"id": 5, "chyron_background_color_2": "#134768"},
    )


def test_migration_with_primary_set_in_theme(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"id": 1, "theme_id": 2, "theme_ids": [2]},
        },
        {
            "type": "create",
            "fqid": "theme/2",
            "fields": {
                "id": 2,
                "organization_id": 1,
                "theme_for_organization_id": 1,
                "primary_500": "#141e28",  # (20, 30, 40) -> (1, 3, 6) -> (5, 9, 14) -> #05090e
            },
        },
        *projector_events,
        {
            "type": "create",
            "fqid": "projector/6",
            "fields": {
                "id": 6,
                "chyron_background_color": "#141e28",
            },
        }
    )

    finalize("0053_fill_new_color_fields")

    assert_model(
        "projector/3",
        {
            "id": 3,
            "chyron_background_color": "#c8dcf0",
            "chyron_font_color": "#ffffff",
            "chyron_background_color_2": "#a7c4e4",
            "chyron_font_color_2": "#ffffff",
        },
    )
    assert_model(
        "projector/4",
        {
            "id": 4,
            "chyron_font_color": "#000000",
            "chyron_background_color_2": "#05090e",
            "chyron_font_color_2": "#000000",
        },
    )
    assert_model(
        "projector/5",
        {"id": 5, "chyron_background_color_2": "#05090e"},
    )
    assert_model(
        "projector/6",
        {
            "id": 6,
            "chyron_background_color": "#141e28",
            "chyron_background_color_2": "#05090e",
        },
    )


def test_migration_with_headbar_set_in_theme(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {"id": 1, "theme_id": 2, "theme_ids": [2]},
        },
        {
            "type": "create",
            "fqid": "theme/2",
            "fields": {
                "id": 2,
                "organization_id": 1,
                "theme_for_organization_id": 1,
                "primary_500": "#141e28",  # (20, 30, 40) -> (1, 3, 6) -> #010306
                "headbar": "#ff0000",
            },
        },
        *projector_events,
        {
            "type": "create",
            "fqid": "projector/6",
            "fields": {
                "id": 6,
                "chyron_background_color": "#141e28",
            },
        }
    )

    finalize("0053_fill_new_color_fields")

    assert_model(
        "projector/3",
        {
            "id": 3,
            "chyron_background_color": "#c8dcf0",
            "chyron_font_color": "#ffffff",
            "chyron_background_color_2": "#a7c4e4",
            "chyron_font_color_2": "#ffffff",
        },
    )
    assert_model(
        "projector/4",
        {
            "id": 4,
            "chyron_font_color": "#000000",
            "chyron_background_color_2": "#ff0000",
            "chyron_font_color_2": "#000000",
        },
    )
    assert_model(
        "projector/5",
        {
            "id": 5,
            "chyron_background_color_2": "#ff0000",
        },
    )
    assert_model(
        "projector/6",
        {
            "id": 6,
            "chyron_background_color": "#141e28",
            "chyron_background_color_2": "#ff0000",
        },
    )
