def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {},
        }
    )
    write(
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {"state_extension": "test [motion:1]"},
        }
    )
    write(
        {
            "type": "update",
            "fqid": "motion/2",
            "fields": {
                "recommendation_extension": "test [motion/1]",
                "state_extension": "test2 [motion:1]",
            },
        }
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/2",
        }
    )
    write(
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {"state_extension": "test [motion/1]"},
        },
        {
            "type": "update",
            "fqid": "motion/3",
            "fields": {"recommendation_extension": "test [motion:1]"},
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/1",
        }
    )
    # test with non-existent motion
    write(
        {
            "type": "update",
            "fqid": "motion/3",
            "fields": {"recommendation_extension": "test [motion:42]"},
        }
    )
    # remove motion/42 from extensions to satisfy the checker
    write(
        {
            "type": "update",
            "fqid": "motion/3",
            "fields": {"state_extension": "test", "recommendation_extension": "test"},
        }
    )

    finalize("0035_fix_motion_extension_fields")

    assert_model(
        "motion/2",
        {
            "state_extension": "test [motion/1]",
            "state_extension_reference_ids": ["motion/1"],
        },
        position=2,
    )
    assert_model(
        "motion/1",
        {"referenced_in_motion_state_extension_ids": [2]},
        position=2,
    )
    assert_model(
        "motion/2",
        {
            "state_extension": "test2 [motion/1]",
            "state_extension_reference_ids": ["motion/1"],
            "recommendation_extension": "test [motion/1]",
            "recommendation_extension_reference_ids": ["motion/1"],
        },
        position=3,
    )
    assert_model(
        "motion/1",
        {
            "referenced_in_motion_state_extension_ids": [2],
            "referenced_in_motion_recommendation_extension_ids": [2],
        },
        position=3,
    )
    assert_model(
        "motion/1",
        {
            "referenced_in_motion_state_extension_ids": [],
            "referenced_in_motion_recommendation_extension_ids": [],
        },
        position=4,
    )
    assert_model(
        "motion/3",
        {
            "state_extension": "test [motion/1]",
            "state_extension_reference_ids": ["motion/1"],
            "recommendation_extension": "test [motion/1]",
            "recommendation_extension_reference_ids": ["motion/1"],
        },
        position=5,
    )
    assert_model(
        "motion/1",
        {
            "referenced_in_motion_state_extension_ids": [3],
            "referenced_in_motion_recommendation_extension_ids": [3],
        },
        position=5,
    )
    assert_model(
        "motion/3",
        {
            "state_extension": "test [motion/1]",
            "state_extension_reference_ids": [],
            "recommendation_extension": "test [motion/1]",
            "recommendation_extension_reference_ids": [],
        },
        position=6,
    )
    assert_model(
        "motion/3",
        {
            "state_extension": "test [motion/1]",
            "state_extension_reference_ids": [],
            "recommendation_extension": "test [motion/42]",
            "recommendation_extension_reference_ids": [],
        },
        position=7,
    )


def test_delete_reference_self(write, finalize):
    # write the relations directly, only tests the correct relation handling
    write(
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {
                "referenced_in_motion_state_extension_ids": [3],
                "referenced_in_motion_recommendation_extension_ids": [3],
            },
        },
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {
                "referenced_in_motion_state_extension_ids": [3],
                "referenced_in_motion_recommendation_extension_ids": [3],
            },
        },
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {
                "state_extension_reference_ids": ["motion/1", "motion/2", "motion/3"],
                "recommendation_extension_reference_ids": [
                    "motion/1",
                    "motion/2",
                    "motion/3",
                ],
                "referenced_in_motion_state_extension_ids": [3],
                "referenced_in_motion_recommendation_extension_ids": [3],
            },
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "motion/1",
        },
        {
            "type": "delete",
            "fqid": "motion/2",
        },
        {
            "type": "delete",
            "fqid": "motion/3",
        },
    )
    finalize("0035_fix_motion_extension_fields")


def test_double_create(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {"state_extension": "test [motion:2]"},
        },
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {"title": "test"},
        },
    )
    finalize("0035_fix_motion_extension_fields")

    assert_model(
        "motion/1",
        {
            "state_extension": "test [motion/2]",
            "state_extension_reference_ids": ["motion/2"],
        },
        position=1,
    )
    assert_model(
        "motion/2",
        {
            "title": "test",
            "referenced_in_motion_state_extension_ids": [1],
        },
        position=1,
    )
