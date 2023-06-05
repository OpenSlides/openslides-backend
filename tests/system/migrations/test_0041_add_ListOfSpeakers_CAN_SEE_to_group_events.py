def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {"permissions": ["list_of_speakers.can_be_speaker"]},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "group/1",
            "fields": {"permissions": []},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "group/1",
            "fields": {"permissions": ["list_of_speakers.can_be_speaker"]},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "group/1",
            "fields": {"permissions": []},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "group/1",
            "list_fields": {
                "add": {"permissions": ["list_of_speakers.can_be_speaker"]},
                "remove": {},
            },
        }
    )

    finalize("0041_add_ListOfSpeakers_CAN_SEE_to_group_events")

    assert_model(
        "group/1",
        {
            "permissions": [
                "list_of_speakers.can_be_speaker",
                "list_of_speakers.can_see",
            ],
            "meta_deleted": False,
            "meta_position": 1,
        },
        position=1,
    )
    assert_model(
        "group/1",
        {"permissions": [], "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        "group/1",
        {
            "permissions": [
                "list_of_speakers.can_be_speaker",
                "list_of_speakers.can_see",
            ],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "group/1",
        {"permissions": [], "meta_deleted": False, "meta_position": 4},
        position=4,
    )
    assert_model(
        "group/1",
        {
            "permissions": [
                "list_of_speakers.can_be_speaker",
                "list_of_speakers.can_see",
            ],
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
