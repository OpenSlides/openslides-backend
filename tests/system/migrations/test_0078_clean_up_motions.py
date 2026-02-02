def test_simple(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {"name": "exists", "forwarded_motion_ids": [1, 2]},
        },
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {"name": "deleted but in system", "forwarded_motion_ids": [3, 6]},
        },
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {
                "title": "existing origin meeting, rer ok",
                "origin_meeting_id": 1,
                "recommendation_extension_reference_ids": ["motion/2"],
                "referenced_in_motion_recommendation_extension_ids": [2, 3],
            },
        },
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {
                "title": "existing origin meeting, rer not ok",
                "origin_meeting_id": 1,
                "recommendation_extension_reference_ids": [
                    "motion/1",
                    "motion/1",
                    "motion/3",
                ],
                "referenced_in_motion_recommendation_extension_ids": [1, 3],
            },
        },
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {
                "title": "nonexistant origin meeting, multiple rer ok",
                "origin_meeting_id": 2,
                "recommendation_extension_reference_ids": ["motion/1", "motion/2"],
                "referenced_in_motion_recommendation_extension_ids": [2],
            },
        },
        {
            "type": "create",
            "fqid": "motion/4",
            "fields": {
                "title": "all explicitly empty",
                "origin_meeting_id": None,
                "recommendation_extension_reference_ids": [],
                "referenced_in_motion_recommendation_extension_ids": [],
            },
        },
        {
            "type": "create",
            "fqid": "motion/5",
            "fields": {
                "title": "mt2",
            },
        },
        {
            "type": "create",
            "fqid": "motion/6",
            "fields": {
                "title": "hekkin' broken, but deleted anyway",
                "origin_meeting_id": 2,
                "recommendation_extension_reference_ids": ["motion/3", "motion/3"],
            },
        },
    )
    write(
        {"type": "delete", "fqid": "meeting/2"},
        {"type": "delete", "fqid": "motion/6"},
    )

    finalize("0078_clean_up_motions")

    assert_model("meeting/1", {"name": "exists", "forwarded_motion_ids": [1, 2]})
    assert_model(
        "meeting/2",
        {
            "name": "deleted but in system",
            "forwarded_motion_ids": [3, 6],
            "meta_deleted": True,
        },
    )

    assert_model(
        "motion/1",
        {
            "title": "existing origin meeting, rer ok",
            "origin_meeting_id": 1,
            "recommendation_extension_reference_ids": ["motion/2"],
            "referenced_in_motion_recommendation_extension_ids": [2, 3],
        },
    )
    assert_model(
        "motion/2",
        {
            "title": "existing origin meeting, rer not ok",
            "origin_meeting_id": 1,
            "recommendation_extension_reference_ids": ["motion/1", "motion/3"],
            "referenced_in_motion_recommendation_extension_ids": [1, 3],
        },
    )
    assert_model(
        "motion/3",
        {
            "title": "nonexistant origin meeting, multiple rer ok",
            "recommendation_extension_reference_ids": ["motion/1", "motion/2"],
            "referenced_in_motion_recommendation_extension_ids": [2],
        },
    )
    assert_model(
        "motion/4",
        {
            "title": "all explicitly empty",
            "recommendation_extension_reference_ids": [],
            "referenced_in_motion_recommendation_extension_ids": [],
        },
    )
    assert_model(
        "motion/5",
        {
            "title": "mt2",
        },
    )
    assert_model(
        "motion/6",
        {
            "title": "hekkin' broken, but deleted anyway",
            "origin_meeting_id": 2,
            "recommendation_extension_reference_ids": ["motion/3", "motion/3"],
            "meta_deleted": True,
        },
    )
