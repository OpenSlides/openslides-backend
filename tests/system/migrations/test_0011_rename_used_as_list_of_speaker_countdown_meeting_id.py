def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": "meeting/1", "fields": {"id": 1}})
    write(
        {
            "type": "create",
            "fqid": "projector_countdown/1",
            "fields": {"id": 1, "used_as_list_of_speaker_countdown_meeting_id": 1},
        }
    )

    finalize("0011_rename_used_as_list_of_speaker_countdown_meeting_id")

    assert_model(
        "projector_countdown/1",
        {
            "id": 1,
            "used_as_list_of_speakers_countdown_meeting_id": 1,
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
