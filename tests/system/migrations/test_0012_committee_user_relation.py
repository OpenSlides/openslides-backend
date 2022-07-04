def test_user_group_create_delete_restore_update_one_position(
    write, finalize, assert_model
):
    write(
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"user_ids": [], "meeting_ids": [10]},
        },
        {
            "type": "create",
            "fqid": "committee/2",
            "fields": {"user_ids": [], "meeting_ids": [20]},
        },
        {
            "type": "create",
            "fqid": "meeting/10",
            "fields": {"committee_id": 1, "group_ids": [100]},
        },
        {
            "type": "create",
            "fqid": "meeting/20",
            "fields": {"committee_id": 2, "group_ids": [200]},
        },
        {"type": "create", "fqid": "group/100", "fields": {"meeting_id": 10}},
        {"type": "create", "fqid": "group/200", "fields": {"meeting_id": 20}},
    )
    write(
        {
            "type": "create",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": [100], "group_$_ids": ["10"]},
        }
    )
    write({"type": "delete", "fqid": "user/1000"})
    write({"type": "restore", "fqid": "user/1000"})
    write(
        {
            "type": "update",
            "fqid": "user/1000",
            "fields": {
                "group_$10_ids": None,
                "group_$20_ids": [200],
                "group_$_ids": ["20"],
            },
        }
    )

    finalize("0012_committee_user_relation")

    assert_model(
        "committee/1",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "user_ids": [],
            "meeting_ids": [10],
        },
        position=1,
    )
    assert_model(
        "committee/2",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "user_ids": [],
            "meeting_ids": [20],
        },
        position=1,
    )

    # user created
    assert_model(
        "committee/1",
        {
            "user_ids": [1000],
            "meeting_ids": [10],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 2,
            "group_$10_ids": [100],
            "group_$_ids": ["10"],
        },
        position=2,
    )

    # user deleted
    assert_model(
        "committee/1",
        {
            "user_ids": [],
            "meeting_ids": [10],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": True,
            "meta_position": 3,
            "group_$10_ids": [100],
            "group_$_ids": ["10"],
        },
        position=3,
    )

    # user restored
    assert_model(
        "committee/1",
        {
            "user_ids": [1000],
            "meeting_ids": [10],
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 4,
            "group_$10_ids": [100],
            "group_$_ids": ["10"],
        },
        position=4,
    )

    # user updated
    assert_model(
        "committee/1",
        {
            "user_ids": [],
            "meeting_ids": [10],
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "committee/2",
        {
            "user_ids": [1000],
            "meeting_ids": [20],
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [2],
            "meta_deleted": False,
            "meta_position": 5,
            "group_$20_ids": [200],
            "group_$_ids": ["20"],
        },
        position=5,
    )


def test_user_committee_management_level_create_delete_restore_update_one_position(
    write, finalize, assert_model
):
    write(
        {"type": "create", "fqid": "committee/1", "fields": {"user_ids": []}},
        {"type": "create", "fqid": "committee/2", "fields": {"user_ids": []}},
    )
    write(
        {
            "type": "create",
            "fqid": "user/1000",
            "fields": {
                "committee_$_management_level": ["1"],
                "committee_$1_management_level": "can_manage",
            },
        }
    )
    write({"type": "delete", "fqid": "user/1000"})
    write({"type": "restore", "fqid": "user/1000"})
    write(
        {
            "type": "update",
            "fqid": "user/1000",
            "fields": {
                "committee_$_management_level": ["2"],
                "committee_$1_management_level": None,
                "committee_$2_management_level": "can_manage",
            },
        }
    )

    finalize("0012_committee_user_relation")

    assert_model(
        "committee/1",
        {"meta_deleted": False, "meta_position": 1, "user_ids": []},
        position=1,
    )
    assert_model(
        "committee/2",
        {"meta_deleted": False, "meta_position": 1, "user_ids": []},
        position=1,
    )

    # user created
    assert_model(
        "committee/1",
        {
            "user_ids": [1000],
            "user_$can_manage_management_level": [1000],
            "user_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 2,
            "committee_$can_manage_management_level": [1],
            "committee_$_management_level": ["can_manage"],
        },
        position=2,
    )

    # user deleted
    assert_model(
        "committee/1",
        {
            "user_ids": [],
            "user_$can_manage_management_level": [],
            "user_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "committee_$can_manage_management_level": [1],
            "committee_$_management_level": ["can_manage"],
            "meta_deleted": True,
            "meta_position": 3,
        },
        position=3,
    )

    # user restored
    assert_model(
        "committee/1",
        {
            "user_ids": [1000],
            "user_$can_manage_management_level": [1000],
            "user_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 4,
        },
        position=4,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 4,
            "committee_$can_manage_management_level": [1],
            "committee_$_management_level": ["can_manage"],
        },
        position=4,
    )

    # user updated
    assert_model(
        "committee/1",
        {
            "user_ids": [],
            "user_$can_manage_management_level": [],
            "user_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "committee/2",
        {
            "user_ids": [1000],
            "user_$can_manage_management_level": [1000],
            "user_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [2],
            "committee_$can_manage_management_level": [2],
            "committee_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 5,
        },
        position=5,
    )


def test_user_mixed_cml_and_group(read_model, write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"user_ids": [], "meeting_ids": [10]},
        },
        {
            "type": "create",
            "fqid": "committee/2",
            "fields": {"user_ids": [], "meeting_ids": [20]},
        },
        {
            "type": "create",
            "fqid": "meeting/10",
            "fields": {"committee_id": 1, "group_ids": [100]},
        },
        {
            "type": "create",
            "fqid": "meeting/20",
            "fields": {"committee_id": 2, "group_ids": [200]},
        },
        {"type": "create", "fqid": "group/100", "fields": {"meeting_id": 10}},
        {"type": "create", "fqid": "group/200", "fields": {"meeting_id": 20}},
    )

    # create user/1000 with groups in committee/1 and /2 and cml for committe/1
    # create user/1001 with group in committee/1 and cml for committee/1 and /2
    write(
        {
            "type": "create",
            "fqid": "user/1000",
            "fields": {
                "group_$_ids": ["10", "20"],
                "group_$10_ids": [100],
                "group_$20_ids": [200],
                "committee_$_management_level": ["1"],
                "committee_$1_management_level": "can_manage",
            },
        },
        {
            "type": "create",
            "fqid": "user/1001",
            "fields": {
                "group_$_ids": ["10"],
                "group_$10_ids": [100],
                "committee_$_management_level": ["1", "2"],
                "committee_$1_management_level": "can_manage",
                "committee_$2_management_level": "can_manage",
            },
        },
    )

    # user/1000 remove group 100
    # user/1001 remove can_manage from committee2
    write(
        {
            "type": "update",
            "fqid": "user/1000",
            "fields": {
                "group_$10_ids": None,
                "group_$_ids": ["20"],
            },
        },
        {
            "type": "update",
            "fqid": "user/1001",
            "fields": {
                "committee_$_management_level": ["1"],
                "committee_$2_management_level": None,
            },
        },
    )

    finalize("0012_committee_user_relation")

    # create user/1000 with groups in committee/1 and /2 and cml for committe/1
    # create user/1001 with group in committee/1 and cml for committee/1 and /2
    assert_model(
        "committee/1",
        {
            "user_ids": [1000, 1001],
            "user_$_management_level": ["can_manage"],
            "user_$can_manage_management_level": [1000, 1001],
            "meeting_ids": [10],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "committee/2",
        {
            "user_ids": [1000, 1001],
            "user_$_management_level": ["can_manage"],
            "user_$can_manage_management_level": [1001],
            "meeting_ids": [20],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "user/1000",
        {
            "group_$_ids": ["10", "20"],
            "group_$10_ids": [100],
            "group_$20_ids": [200],
            "committee_ids": [1, 2],
            "committee_$can_manage_management_level": [1],
            "committee_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "user/1001",
        {
            "group_$_ids": ["10"],
            "group_$10_ids": [100],
            "committee_ids": [1, 2],
            "committee_$can_manage_management_level": [1, 2],
            "committee_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )

    # user/1000 remove group 100
    # user/1001 remove can_manage from committee2
    assert_model(
        "committee/1",
        {
            "user_ids": [1000, 1001],
            "user_$_management_level": ["can_manage"],
            "user_$can_manage_management_level": [1000, 1001],
            "meeting_ids": [10],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "committee/2",
        {
            "user_ids": [1000],
            "user_$_management_level": ["can_manage"],
            "user_$can_manage_management_level": [],
            "meeting_ids": [20],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "user/1000",
        {
            "group_$_ids": ["20"],
            "group_$20_ids": [200],
            "committee_ids": [1, 2],
            "committee_$can_manage_management_level": [1],
            "committee_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )
    assert_model(
        "user/1001",
        {
            "group_$_ids": ["10"],
            "group_$10_ids": [100],
            "committee_ids": [1],
            "committee_$can_manage_management_level": [1],
            "committee_$_management_level": ["can_manage"],
            "meta_deleted": False,
            "meta_position": 3,
        },
        position=3,
    )


def test_user_add_remove_add(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"user_ids": [], "meeting_ids": [10]},
        },
        {
            "type": "create",
            "fqid": "meeting/10",
            "fields": {"committee_id": 1, "group_ids": [100]},
        },
        {"type": "create", "fqid": "group/100", "fields": {"meeting_id": 10}},
    )
    write(
        {
            "type": "create",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": [100], "group_$_ids": ["10"]},
        },
        {
            "type": "update",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": None, "group_$_ids": []},
        },
        {
            "type": "update",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": [100], "group_$_ids": ["10"]},
        },
    )

    finalize("0012_committee_user_relation")

    assert_model(
        "committee/1",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "user_ids": [],
            "meeting_ids": [10],
        },
        position=1,
    )

    # user data changed
    assert_model(
        "committee/1",
        {
            "user_ids": [1000],
            "meeting_ids": [10],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 2,
            "group_$10_ids": [100],
            "group_$_ids": ["10"],
        },
        position=2,
    )


def test_user_remove_add(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"user_ids": [1000], "meeting_ids": [10]},
        },
        {
            "type": "create",
            "fqid": "meeting/10",
            "fields": {"committee_id": 1, "group_ids": [100]},
        },
        {"type": "create", "fqid": "group/100", "fields": {"meeting_id": 10}},
        {
            "type": "create",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": [100], "group_$_ids": ["10"]},
        },
    )
    write(
        {
            "type": "update",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": None, "group_$_ids": []},
        },
        {
            "type": "update",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": [100], "group_$_ids": ["10"]},
        },
    )

    finalize("0012_committee_user_relation")

    assert_model(
        "committee/1",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "user_ids": [1000],
            "meeting_ids": [10],
        },
        position=1,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 1,
            "group_$10_ids": [100],
            "group_$_ids": ["10"],
        },
        position=1,
    )

    # user data changed
    assert_model(
        "committee/1",
        {
            "user_ids": [1000],
            "meeting_ids": [10],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 2,
            "group_$10_ids": [100],
            "group_$_ids": ["10"],
        },
        position=2,
    )


def test_user_remove_add_2_stages(migrate, write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"user_ids": [], "meeting_ids": [10]},
        },
        {
            "type": "create",
            "fqid": "meeting/10",
            "fields": {"committee_id": 1, "group_ids": [100]},
        },
        {"type": "create", "fqid": "group/100", "fields": {"meeting_id": 10}},
        {
            "type": "create",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": [100], "group_$_ids": ["10"]},
        },
    )
    migrate("0012_committee_user_relation")

    write(
        {
            "type": "update",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": None, "group_$_ids": []},
        },
        {
            "type": "update",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": [100], "group_$_ids": ["10"]},
        },
    )

    finalize("0012_committee_user_relation")

    assert_model(
        "committee/1",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "user_ids": [1000],
            "meeting_ids": [10],
        },
        position=1,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 1,
            "group_$10_ids": [100],
            "group_$_ids": ["10"],
        },
        position=1,
    )

    # user data changed
    assert_model(
        "committee/1",
        {
            "user_ids": [1000],
            "meeting_ids": [10],
            "meta_deleted": False,
            "meta_position": 2,
        },
        position=2,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 2,
            "group_$10_ids": [100],
            "group_$_ids": ["10"],
        },
        position=2,
    )


def test_events_in_wrong_sequence(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "user/1000",
            "fields": {"group_$10_ids": [100], "group_$_ids": ["10"]},
        },
        {"type": "create", "fqid": "group/100", "fields": {"meeting_id": 10}},
        {
            "type": "create",
            "fqid": "meeting/10",
            "fields": {"committee_id": 1, "group_ids": [100]},
        },
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {"user_ids": [1000], "meeting_ids": [10]},
        },
    )

    finalize("0012_committee_user_relation")

    assert_model(
        "committee/1",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "user_ids": [1000],
            "meeting_ids": [10],
        },
        position=1,
    )
    assert_model(
        "user/1000",
        {
            "committee_ids": [1],
            "meta_deleted": False,
            "meta_position": 1,
            "group_$10_ids": [100],
            "group_$_ids": ["10"],
        },
        position=1,
    )


def test_with_shortened_example_data(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {
                "committee_ids": [1],
                "committee_$_management_level": ["1"],
                "committee_$1_management_level": ["can_manage"],
                "group_$_ids": ["1"],
                "group_$1_ids": [2],
            },
        },
        {
            "type": "create",
            "fqid": "user/2",
            "fields": {
                "committee_ids": [1],
                "committee_$_management_level": [],
                "group_$_ids": ["1"],
                "group_$1_ids": [5],
            },
        },
        {
            "type": "create",
            "fqid": "user/3",
            "fields": {
                "committee_ids": [],
                "committee_$_management_level": [],
                "group_$_ids": ["1"],
                "group_$1_ids": [5],
            },
        },
        {
            "type": "create",
            "fqid": "committee/1",
            "fields": {
                "user_ids": [1, 2],
                "meeting_ids": [1],
            },
        },
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "committee_id": 1,
                "group_ids": [1, 2, 3, 4, 5],
                "user_ids": [1, 2, 3],
                "default_group_id": 1,
                "admin_group_id": 2,
                "is_active_in_organization_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "meeting_id": 1,
                "user_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "group/2",
            "fields": {
                "meeting_id": 1,
                "user_ids": [1],
            },
        },
        {
            "type": "create",
            "fqid": "group/3",
            "fields": {
                "meeting_id": 1,
                "user_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "group/4",
            "fields": {
                "meeting_id": 1,
                "user_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "group/5",
            "fields": {
                "meeting_id": 1,
                "user_ids": [2, 3],
            },
        },
    )

    finalize("0012_committee_user_relation")

    assert_model(
        "committee/1",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "user_ids": [1, 2, 3],
            "meeting_ids": [1],
            "user_$_management_level": ["can_manage"],
            "user_$can_manage_management_level": [1],
        },
        position=1,
    )

    assert_model(
        "user/1",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "committee_ids": [1],
            "committee_$_management_level": ["can_manage"],
            "committee_$can_manage_management_level": [1],
            "group_$_ids": ["1"],
            "group_$1_ids": [2],
        },
        position=1,
    )

    assert_model(
        "user/2",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "committee_ids": [1],
            "committee_$_management_level": [],
            "group_$_ids": ["1"],
            "group_$1_ids": [5],
        },
        position=1,
    )

    assert_model(
        "user/3",
        {
            "meta_deleted": False,
            "meta_position": 1,
            "committee_ids": [1],
            "committee_$_management_level": [],
            "group_$_ids": ["1"],
            "group_$1_ids": [5],
        },
        position=1,
    )
