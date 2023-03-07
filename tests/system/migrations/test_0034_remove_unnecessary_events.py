from copy import deepcopy


def setup_data(write):
    # Create models
    write(
        {
            "type": "create",
            "fqid": "dummy/1",
            "fields": {
                "fqid": "dummy/1",
                "f1": "test",
                "f2": [1, 2, 3],
                "f3": 42,
                "f4": [1],
            },
        },
        {
            "type": "create",
            "fqid": "other/2",
            "fields": {
                "fqid": "other/2",
                "f1": "test",
                "f2": [1, 2, 3],
                "f3": 42,
                "f4": [1],
            },
        },
    )
    write(
        # Partial update
        {
            "type": "update",
            "fqid": "dummy/1",
            "fields": {"f1": "value", "f2": [1, 2, 3]},
        },
        # redundant update
        {
            "type": "update",
            "fqid": "other/2",
            "fields": {"f1": "test"},
        },
    )
    write(
        # double redundant update
        {
            "type": "update",
            "fqid": "dummy/1",
            "fields": {"f1": "value", "f3": 42},
        },
    )
    write(
        # necessary list_fields update add
        {
            "type": "update",
            "fqid": "dummy/1",
            "list_fields": {"add": {"f2": [4]}},
        },
        # necessary list_fields update remove
        {
            "type": "update",
            "fqid": "other/2",
            "list_fields": {"remove": {"f2": [3]}},
        },
    )
    write(
        # redundant list_fields update add
        {
            "type": "update",
            "fqid": "dummy/1",
            "list_fields": {"add": {"f2": [4]}},
        },
        # redundant list_fields update remove
        {
            "type": "update",
            "fqid": "other/2",
            "list_fields": {"remove": {"f2": [3]}},
        },
    )
    write(
        # redundant list_fields update both
        {
            "type": "update",
            "fqid": "dummy/1",
            "list_fields": {"add": {"f2": [4]}, "remove": {"f2": [5]}},
        },
        # necessary add, redundant remove
        {
            "type": "update",
            "fqid": "other/2",
            "list_fields": {"add": {"f2": [3]}, "remove": {"f2": [4]}},
        },
    )
    write(
        # partially necessary add
        {
            "type": "update",
            "fqid": "dummy/1",
            "list_fields": {"add": {"f2": [4], "f4": [2]}},
        },
        # partially necessary remove
        {
            "type": "update",
            "fqid": "other/2",
            "list_fields": {"remove": {"f2": [3], "f4": [2]}},
        },
    )
    write(
        # necessary deletefields
        {
            "type": "update",
            "fqid": "dummy/1",
            "fields": {"f1": None},
        },
        # partially necessary deletefields
        {
            "type": "update",
            "fqid": "other/2",
            "fields": {"f1": None, "fx": None},
        },
    )
    write(
        # redundant deletefields
        {
            "type": "update",
            "fqid": "dummy/1",
            "fields": {"f1": None},
        },
    )


def check_models(assert_model, redundant_updates):
    def check(data, position):
        assert_model(
            data["fqid"],
            data,
            position=position,
        )

    dummy_data = {
        "fqid": "dummy/1",
        "f1": "test",
        "f2": [1, 2, 3],
        "f3": 42,
        "f4": [1],
        "meta_deleted": False,
        "meta_position": 1,
    }
    other_data = deepcopy(dummy_data)
    other_data["fqid"] = "other/2"
    check(dummy_data, 1)
    check(other_data, 1)
    dummy_data["f1"] = "value"
    dummy_data["meta_position"] = 2
    if redundant_updates:
        other_data["meta_position"] = 2
    check(dummy_data, 2)
    check(other_data, 2)
    if redundant_updates:
        dummy_data["meta_position"] = 3
    check(dummy_data, 3)
    check(other_data, 3)
    dummy_data["f2"] = [1, 2, 3, 4]
    other_data["f2"] = [1, 2]
    dummy_data["meta_position"] = other_data["meta_position"] = 4
    check(dummy_data, 4)
    check(other_data, 4)
    if redundant_updates:
        dummy_data["meta_position"] = other_data["meta_position"] = 5
    check(dummy_data, 5)
    check(other_data, 5)
    other_data["f2"] = [1, 2, 3]
    other_data["meta_position"] = 6
    if redundant_updates:
        dummy_data["meta_position"] = 6
    check(dummy_data, 6)
    check(other_data, 6)
    dummy_data["f4"] = [1, 2]
    other_data["f2"] = [1, 2]
    dummy_data["meta_position"] = other_data["meta_position"] = 7
    check(dummy_data, 7)
    check(other_data, 7)
    del dummy_data["f1"]
    del other_data["f1"]
    dummy_data["meta_position"] = other_data["meta_position"] = 8
    check(dummy_data, 8)
    check(other_data, 8)
    if redundant_updates:
        dummy_data["meta_position"] = 9
    check(dummy_data, 9)


def test_migration(write, finalize, assert_model):
    setup_data(write)
    check_models(assert_model, True)
    finalize("0034_remove_unnecessary_events")
    check_models(assert_model, False)
