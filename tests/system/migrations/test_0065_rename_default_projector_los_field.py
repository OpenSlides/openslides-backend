def create_data():
    return {
        "meeting/1": {
            "id": 1,
            "name": "Meeting 1",
            "all_projection_ids": [3],
            "projection_ids": [3],
            "projector_ids": [2],
            "default_projector_current_list_of_speakers_ids": [2],
        },
        "projector/2": {
            "id": 2,
            "projection_id": 3,
            "meeting_id": 1,
            "used_as_default_projector_for_current_list_of_speakers_in_meeting_id": 1,
        },
        "projection/3": {
            "id": 3,
            "projector_id": 2,
            "type": "current_list_of_speakers",
            "content_object_id": "meeting/1",
            "meeting_id": 1,
        },
    }


def write_data(write, data):
    for fqid, fields in data.items():
        write({"type": "create", "fqid": fqid, "fields": fields})


def assert_data(assert_model, data):
    for fqid, fields in data.items():
        assert_model(fqid, fields)


def test_migration_simple(write, finalize, assert_model):
    data = create_data()
    write_data(write, data)

    finalize("0065_rename_default_projector_los_field")

    data["meeting/1"]["default_projector_current_los_ids"] = [2]
    del data["meeting/1"]["default_projector_current_list_of_speakers_ids"]
    data["projector/2"]["used_as_default_projector_for_current_los_in_meeting_id"] = 1
    del data["projector/2"][
        "used_as_default_projector_for_current_list_of_speakers_in_meeting_id"
    ]
    data["projection/3"]["type"] = "current_los"

    assert_data(assert_model, data)


def test_migration_deleted(write, finalize, assert_model):
    data = create_data()
    data["projector/4"] = {
        "id": 4,
        "projection_id": 4,
        "meeting_id": 1,
        "used_as_default_projector_for_current_list_of_speakers_in_meeting_id": 1,
    }
    data["projection/5"] = {
        "id": 5,
        "projector_id": 4,
        "type": "current_list_of_speakers",
        "content_object_id": "meeting/1",
        "meeting_id": 1,
    }
    data["meeting/1"].update(
        {
            "all_projection_ids": [3],
            "projection_ids": [3],
            "projector_ids": [2],
            "default_projector_current_los_ids": [2],
        }
    )

    write_data(write, data)
    write(
        {"type": "delete", "fqid": "projector/4", "fields": {}},
        {"type": "delete", "fqid": "projection/5"},
    )

    finalize("0065_rename_default_projector_los_field")

    data["meeting/1"]["default_projector_current_los_ids"] = [2]
    del data["meeting/1"]["default_projector_current_list_of_speakers_ids"]
    data["projector/2"]["used_as_default_projector_for_current_los_in_meeting_id"] = 1
    del data["projector/2"][
        "used_as_default_projector_for_current_list_of_speakers_in_meeting_id"
    ]
    data["projector/4"]["meta_deleted"] = True
    data["projection/3"]["type"] = "current_los"
    data["projection/5"]["meta_deleted"] = True
    assert_data(assert_model, data)


def test_migration_broken_relation(write, finalize, assert_model):
    data = create_data()
    data["projector/4"] = {
        "id": 4,
        "projection_id": 4,
        "meeting_id": 1,
        "used_as_default_projector_for_current_list_of_speakers_in_meeting_id": 1,
    }
    data["projection/5"] = {
        "id": 5,
        "projector_id": 4,
        "type": "current_list_of_speakers",
        "content_object_id": "meeting/1",
        "meeting_id": 1,
    }
    data["meeting/1"].update(
        {
            "all_projection_ids": [3, 5],
            "projection_ids": [3, 5],
            "projector_ids": [2, 4],
        }
    )
    write_data(write, data)

    finalize("0065_rename_default_projector_los_field")

    data["meeting/1"]["default_projector_current_los_ids"] = [2]
    del data["meeting/1"]["default_projector_current_list_of_speakers_ids"]
    data["projector/2"]["used_as_default_projector_for_current_los_in_meeting_id"] = 1
    del data["projector/2"][
        "used_as_default_projector_for_current_list_of_speakers_in_meeting_id"
    ]
    del data["projector/4"][
        "used_as_default_projector_for_current_list_of_speakers_in_meeting_id"
    ]
    data["projection/3"]["type"] = "current_los"
    data["projection/5"]["type"] = "current_los"
    assert_data(assert_model, data)


def test_migration_field_not_set(write, finalize, assert_model):
    data = create_data()
    data["projector/4"] = {
        "id": 4,
        "projection_id": 4,
        "meeting_id": 1,
    }
    data["projection/5"] = {
        "id": 5,
        "projector_id": 4,
        "type": "motion",
        "content_object_id": "motion/6",
        "meeting_id": 1,
    }
    data["motion/6"] = {"id": 6, "projection_ids": [5]}
    data["meeting/1"].update(
        {
            "all_projection_ids": [3, 5],
            "projection_ids": [3],
            "projector_ids": [2, 4],
        }
    )
    write_data(write, data)

    finalize("0065_rename_default_projector_los_field")

    data["meeting/1"]["default_projector_current_los_ids"] = [2]
    del data["meeting/1"]["default_projector_current_list_of_speakers_ids"]
    data["projector/2"]["used_as_default_projector_for_current_los_in_meeting_id"] = 1
    del data["projector/2"][
        "used_as_default_projector_for_current_list_of_speakers_in_meeting_id"
    ]
    data["projection/3"]["type"] = "current_los"
    assert_data(assert_model, data)
