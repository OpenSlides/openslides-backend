from math import floor
from typing import Any


def get_muser(
    id_: int, additional_data: dict[str, Any] = {}
) -> dict[int, dict[str, Any]]:
    return {
        id_: {"meeting_id": floor(id_ / 10), "user_id": id_ % 10, **additional_data}
    }


def get_motion(
    id_: int, additional_data: dict[str, Any] = {}
) -> dict[int, dict[str, Any]]:
    return {
        id_: {
            "meeting_id": floor(id_ / 10),
            "title": f"Motion {id_%10}",
            "list_of_speakers_id": (id_ % 10) * 10 + floor(id_ / 10),
            **additional_data,
        }
    }


def get_los(
    id_: int, additional_data: dict[str, Any] = {}
) -> dict[int, dict[str, Any]]:
    return {
        id_: {
            "meeting_id": id_ % 10,
            "sequential_number": floor(id_ / 10),
            "content_object_id": f"motion/{(id_%10)*10+floor(id_/10)}",
            **additional_data,
        }
    }


def get_speaker(
    id_: int, additional_data: dict[str, Any] = {}
) -> dict[int, dict[str, Any]]:
    return {
        id_: {
            "meeting_id": floor(id_ / 100) % 10,
            "list_of_speakers_id": floor(id_ / 100),
            "meeting_user_id": id_ % 100,
            **additional_data,
        }
    }


def get_sllos(
    id_: int, additional_data: dict[str, Any] = {}
) -> dict[int, dict[str, Any]]:
    return {
        id_: {
            "meeting_id": (floor(id_ / 10) % 10),
            "structure_level_id": id_ % 10,
            "list_of_speakers_id": floor(id_ / 10),
            **additional_data,
        }
    }


MOTION_MEETING_USER_MODELS = [
    "motion_editor",
    "motion_working_group_speaker",
    "motion_submitter",
]

# TODO: Write test with minimal data.
# TODO: Write test with no intact target models found.


def test_migration_complex(write, finalize, assert_model):
    to_delete = [
        "user/4",
        "meeting/4",
        "meeting_user/22",
        "motion/14",
        "personal_note/4",
        "list_of_speakers/41",
        "assignment_candidate/4",
        "chat_message/8",
        "structure_level/4",
        "point_of_order_category/3",
        "speaker/1111",
        "structure_level_list_of_speakers/311",
        *[f"{collection}/4" for collection in MOTION_MEETING_USER_MODELS],
    ]
    collection_to_id_to_data: dict[str, dict[int, dict[str, Any]]] = {
        "meeting": {
            1: {
                "name": "City hall",
                "list_of_speakers_countdown_id": 1,
                "projector_countdown_ids": [1],
                "group_ids": [1],
                "meeting_user_ids": [11, 12, 13, 14, 15, 16],
                "motion_ids": [11, 12, 13, 15],
                "list_of_speakers_ids": [11, 21, 31, 51],
                "personal_note_ids": [3],
                "chat_message_ids": [1, 2, 3, 4, 5, 6, 7, 9, 10],
                "structure_level_ids": [1, 2, 3],
                "point_of_order_category_ids": [1, 2],
                "speaker_ids": [
                    1112,
                    1113,
                    1114,
                    2111,
                    2115,
                    2116,
                    3111,
                    3116,
                    4111,
                    5115,
                ],
                **{
                    f"{collection}_ids": [1, 2]
                    for collection in MOTION_MEETING_USER_MODELS
                },
                "structure_level_list_of_speakers_ids": [111, 112, 113, 211, 512],
            },
            2: {
                "name": "County congress",
                "list_of_speakers_couple_countdown": True,
                "list_of_speakers_countdown_id": 2,
                "projector_countdown_ids": [2],
                "group_ids": [2],
                "meeting_user_ids": [21, 23],
                "personal_note_ids": [1],
                "motion_ids": [21, 22],
                "list_of_speakers_ids": [12, 22],
                "structure_level_ids": [5, 6],
                "speaker_ids": [1221, 1223, 2221],
                "structure_level_list_of_speakers_ids": [125, 126],
            },
            3: {
                "name": "National congress",
                "list_of_speakers_couple_countdown": True,
                "list_of_speakers_countdown_id": 3,
                "projector_countdown_ids": [3],
                "group_ids": [3],
                "meeting_user_ids": [31, 32, 33],
                "motion_ids": [31],
                "list_of_speakers_ids": [13],
                "structure_level_ids": [7, 8, 9],
                "assignment_candidate_ids": [1, 2, 3],
                "speaker_ids": [1331, 1332, 1333],
                **{
                    f"{collection}_ids": [3]
                    for collection in MOTION_MEETING_USER_MODELS
                },
                "structure_level_list_of_speakers_ids": [139],
            },
            4: {
                "name": "Deleted congress",
                "list_of_speakers_couple_countdown": True,
            },  # delete
        },
        "group": {
            1: {"name": "Group A", "meeting_user_ids": [13], "meeting_id": 1},
            2: {"name": "Group B", "meeting_user_ids": [], "meeting_id": 2},
            3: {"name": "Group C", "meeting_user_ids": [], "meeting_id": 3},
        },
        "projector_countdown": {
            1: {
                "title": "LOS",
                "used_as_list_of_speakers_countdown_meeting_id": 1,
                "meeting_id": 1,
                "default_time": 60,
                "countdown_time": 200,
                "running": True,
            },
            2: {
                "title": "LOS",
                "used_as_list_of_speakers_countdown_meeting_id": 2,
                "meeting_id": 2,
                "default_time": 60,
                "countdown_time": 60,
                "running": False,
            },
            3: {
                "title": "LOS",
                "used_as_list_of_speakers_countdown_meeting_id": 3,
                "meeting_id": 3,
                "default_time": 60,
                "countdown_time": 300,
                "running": True,
            },
        },
        "user": {
            1: {"username": "admin", "meeting_user_ids": [11, 21, 31, 41]},
            2: {"username": "bob", "meeting_user_ids": [12, 32]},
            3: {"username": "charlotte", "meeting_user_ids": [13, 23, 33]},
            4: {"username": "DELETED"},  # delete
            5: {"username": "elizabeth", "meeting_user_ids": [15, 25]},
            6: {"username": "george", "meeting_user_ids": [16]},
        },
        "meeting_user": {
            **get_muser(
                11,
                {
                    "speaker_ids": [1111, 2111, 3111, 4111],
                    "structure_level_ids": [1],
                    "chat_message_ids": [9],
                    "supported_motion_ids": [11, 12, 13],
                },
            ),
            **get_muser(
                12,
                {
                    "vote_delegations_from_ids": [13],
                    "speaker_ids": [1112],
                    "structure_level_ids": [1, 2],
                    "group_ids": [],
                    "supported_motion_ids": [11],
                },
            ),
            **get_muser(
                13,
                {
                    "speaker_ids": [1113],
                    "structure_level_ids": [1, 2],
                    "chat_message_ids": [],
                    "group_ids": [1],
                    "vote_delegated_to_id": 12,
                    "vote_delegations_from_ids": [14, 15, 16],
                    "supported_motion_ids": [11],
                },
            ),
            **get_muser(
                14,
                {
                    "speaker_ids": [1114],
                    "structure_level_ids": [1, 2],
                    "chat_message_ids": [5, 7],
                    "vote_delegated_to_id": 13,
                    **{
                        f"{collection}_ids": [1]
                        for collection in MOTION_MEETING_USER_MODELS
                    },
                },
            ),
            **get_muser(
                15,
                {
                    "speaker_ids": [2115, 5115],
                    "structure_level_ids": [3],
                    "chat_message_ids": [2, 4, 10],
                    "personal_note_ids": [3],
                    "vote_delegated_to_id": 13,
                    **{
                        f"{collection}_ids": [2, 4]
                        for collection in MOTION_MEETING_USER_MODELS
                    },
                },
            ),
            **get_muser(
                16,
                {
                    "vote_delegated_to_id": 13,
                    "speaker_ids": [2116, 3116],
                    "chat_message_ids": [1, 3, 6],
                },
            ),
            **get_muser(
                21,
                {
                    "speaker_ids": [1221, 2221],
                    "structure_level_ids": [4, 5],
                    "assignment_candidate_ids": [4],
                    "personal_note_ids": [1],
                    "vote_delegations_from_ids": [22],
                },
            ),
            **get_muser(
                22, {"vote_delegated_to_id": 21, "vote_delegations_from_ids": [23]}
            ),  # delete
            **get_muser(
                23,
                {
                    "speaker_ids": [1223],
                    "structure_level_ids": [4],
                    "personal_note_ids": [2],
                    "vote_delegated_to_id": 22,
                },
            ),
            **get_muser(25, {"structure_level_ids": [6], "personal_note_ids": [4]}),
            **get_muser(
                31,
                {
                    "speaker_ids": [1331],
                    "structure_level_ids": [7, 9],
                    "assignment_candidate_ids": [1],
                    "vote_delegated_to_id": 32,
                    **{
                        f"{collection}_ids": [3]
                        for collection in MOTION_MEETING_USER_MODELS
                    },
                },
            ),
            **get_muser(
                32,
                {
                    "speaker_ids": [1332],
                    "structure_level_ids": [8],
                    "assignment_candidate_ids": [2],
                    "vote_delegations_from_ids": [31],
                },
            ),
            **get_muser(
                33,
                {
                    "speaker_ids": [1333],
                    "structure_level_ids": [8],
                    "assignment_candidate_ids": [3],
                },
            ),
            **get_muser(41),
        },
        "list_of_speakers": {
            # Opposite id digit order to related motions
            **get_los(
                11,
                {
                    "structure_level_list_of_speakers_ids": [111, 112, 113],
                    "speaker_ids": [1112, 1113, 1114],
                },
            ),
            **get_los(
                21,
                {
                    "structure_level_list_of_speakers_ids": [211],
                    "speaker_ids": [2111, 2115, 2116],
                },
            ),
            **get_los(
                31,
                {
                    "structure_level_list_of_speakers_ids": [],
                    "speaker_ids": [3111, 3116],
                },
            ),
            **get_los(41, {"speaker_ids": [4111]}),  # delete
            **get_los(
                51,
                {"structure_level_list_of_speakers_ids": [512], "speaker_ids": [5115]},
            ),
            **get_los(
                12,
                {
                    "structure_level_list_of_speakers_ids": [125, 126],
                    "speaker_ids": [1221, 1223],
                },
            ),
            **get_los(22, {"speaker_ids": [2221]}),
            **get_los(
                13,
                {
                    "structure_level_list_of_speakers_ids": [139],
                    "speaker_ids": [1331, 1332, 1333],
                },
            ),
        },
        "motion": {
            **get_motion(
                11,
                {
                    **{
                        f"{collection[7:]}_ids": [1, 2]
                        for collection in MOTION_MEETING_USER_MODELS
                    },
                    "supporter_meeting_user_ids": [11, 12, 13],
                },
            ),
            **get_motion(12, {"supporter_meeting_user_ids": [11]}),
            **get_motion(
                13,
                {"personal_note_ids": [3], "supporter_meeting_user_ids": [11]},
            ),
            **get_motion(14),  # delete
            **get_motion(15),
            **get_motion(21, {"personal_note_ids": [1, 2]}),
            **get_motion(22),
            **get_motion(
                31,
                {
                    **{
                        f"{collection[7:]}_ids": [3]
                        for collection in MOTION_MEETING_USER_MODELS
                    }
                },
            ),
        },
        "personal_note": {
            1: {
                "meeting_id": 2,
                "content_object_id": "motion/21",
                "meeting_user_id": 21,
            },
            2: {
                "meeting_id": 2,
                "content_object_id": "motion/21",
                "meeting_user_id": 23,
            },
            3: {
                "meeting_id": 1,
                "content_object_id": "motion/13",
                "meeting_user_id": 15,
            },
            4: {
                "meeting_id": 2,
                "content_object_id": "motion/22",
                "meeting_user_id": 25,
            },  # delete
        },
        # "motion_supporter":{},
        **{
            collection: {
                id_: date
                for id_, date in {
                    1: {
                        "meeting_id": 1,
                        "motion_id": 11,
                        "meeting_user_id": 14,
                        "weight": 1,
                    },
                    2: {
                        "meeting_id": 1,
                        "motion_id": 11,
                        "meeting_user_id": 15,
                        "weight": 2,
                    },
                    3: {
                        "meeting_id": 3,
                        "motion_id": 31,
                        "meeting_user_id": 31,
                        "weight": 1,
                    },
                    4: {
                        "meeting_id": 1,
                        "motion_id": 12,
                        "meeting_user_id": 15,
                        "weight": 1,
                    },  # delete
                }.items()
            }
            for collection in MOTION_MEETING_USER_MODELS
        },
        "assignment_candidate": {
            1: {"meeting_id": 3, "meeting_user_id": 31},
            2: {"meeting_id": 3, "meeting_user_id": 32},
            3: {"meeting_id": 3, "meeting_user_id": 33},
            4: {"meeting_id": 2, "meeting_user_id": 21},  # delete
        },
        "chat_message": {
            1: {
                "meeting_user_id": 16,
                "meeting_id": 1,
                "content": "Hey, any of u up?",
                "created": 100,
            },
            2: {
                "meeting_user_id": 15,
                "meeting_id": 1,
                "content": "I am, wazzup dude?",
                "created": 200,
            },
            3: {
                "meeting_user_id": 16,
                "meeting_id": 1,
                "content": "Wanna go ditch tomorrows conference and go bar hopping?",
                "created": 300,
            },
            4: {
                "meeting_user_id": 15,
                "meeting_id": 1,
                "content": "Absolutely, ma man! Conf's gonna be hella boring anyway...",
                "created": 400,
            },
            5: {
                "meeting_user_id": 14,
                "meeting_id": 1,
                "content": "Yo guys, can I join in?",
                "created": 500,
            },
            6: {
                "meeting_user_id": 16,
                "meeting_id": 1,
                "content": "Why u even asking, bro? Of course!",
                "created": 600,
            },
            7: {
                "meeting_user_id": 14,
                "meeting_id": 1,
                "content": "Totally rad, thx.",
                "created": 700,
            },
            8: {
                "meeting_user_id": 13,
                "meeting_id": 1,
                "content": "Srsly? Do ur jobs for once, will ya?",
                "created": 1100,
            },  # deleted
            9: {
                "meeting_user_id": 11,
                "meeting_id": 1,
                "content": "Have fun everyone, I'll go to the conference and catch you up later.",
                "created": 1200,
            },
            10: {
                "meeting_user_id": 15,
                "meeting_id": 1,
                "content": "You da man!",
                "created": 1300,
            },
        },
        "structure_level": {
            1: {
                "meeting_id": 1,
                "meeting_user_ids": [11, 12, 13, 14],
                "name": "red",
                "color": "#ff0000",
                "structure_level_list_of_speakers_ids": [111, 211],
            },
            2: {
                "meeting_id": 1,
                "meeting_user_ids": [12, 13, 14],
                "name": "green",
                "color": "#00ff00",
                "structure_level_list_of_speakers_ids": [112, 512],
            },
            3: {
                "meeting_id": 1,
                "meeting_user_ids": [15],
                "name": "blue",
                "color": "#0000ff",
                "structure_level_list_of_speakers_ids": [113],
            },
            4: {
                "meeting_id": 2,
                "meeting_user_ids": [21, 22],
                "name": "red",
                "color": "#ff0000",
            },  # delete
            5: {
                "meeting_id": 2,
                "meeting_user_ids": [21],
                "name": "green",
                "color": "#00ff00",
                "structure_level_list_of_speakers_ids": [125],
            },
            6: {
                "meeting_id": 2,
                "meeting_user_ids": [25],
                "name": "blue",
                "color": "#0000ff",
                "structure_level_list_of_speakers_ids": [126],
            },
            7: {
                "meeting_id": 3,
                "meeting_user_ids": [31],
                "name": "red",
                "color": "#ff0000",
            },
            8: {
                "meeting_id": 3,
                "meeting_user_ids": [32, 33],
                "name": "green",
                "color": "#00ff00",
            },
            9: {
                "meeting_id": 3,
                "meeting_user_ids": [31],
                "name": "blue",
                "color": "#0000ff",
                "structure_level_list_of_speakers_ids": [139],
            },
        },
        "point_of_order_category": {
            1: {"text": "A", "rank": 1, "meeting_id": 1, "speaker_ids": [1112, 1113]},
            2: {"text": "B", "rank": 2, "meeting_id": 1, "speaker_ids": [2111]},
            3: {
                "text": "C",
                "rank": 3,
                "meeting_id": 1,
                "speaker_ids": [3111],
            },  # delete
        },
        "speaker": {
            # id_ = los_id * 100 + muser_id
            **get_speaker(
                1111,
                {"structure_level_list_of_speakers_id": 111, "point_of_order": True},
            ),  # delete
            **get_speaker(
                1112,
                {
                    "structure_level_list_of_speakers_id": 112,
                    "point_of_order": True,
                    "point_of_order_category_id": 1,
                },
            ),
            **get_speaker(
                1113,
                {
                    "structure_level_list_of_speakers_id": 112,
                    "point_of_order": True,
                    "point_of_order_category_id": 1,
                },
            ),
            **get_speaker(
                1114,
                {
                    "structure_level_list_of_speakers_id": 113,
                    "speech_state": "intervention",
                },
            ),
            **get_speaker(
                2111,
                {
                    "structure_level_list_of_speakers_id": 211,
                    "point_of_order": True,
                    "point_of_order_category_id": 2,
                },
            ),
            **get_speaker(2115, {"structure_level_list_of_speakers_id": 211}),
            **get_speaker(
                2116,
                {
                    "structure_level_list_of_speakers_id": 211,
                    "speech_state": "interposed_question",
                },
            ),
            **get_speaker(
                3111,
                {
                    "structure_level_list_of_speakers_id": 311,
                    "point_of_order": True,
                    "point_of_order_category_id": 3,
                },
            ),
            **get_speaker(3116, {"speech_state": "pro"}),
            **get_speaker(4111),
            **get_speaker(
                5115,
                {
                    "structure_level_list_of_speakers_id": 512,
                    "begin_time": 100,
                    "pause_time": 200,
                },
            ),
            **get_speaker(1221, {"structure_level_list_of_speakers_id": 125}),
            **get_speaker(1223, {"structure_level_list_of_speakers_id": 126}),
            **get_speaker(2221),
            **get_speaker(1331, {"begin_time": 100, "end_time": 200}),
            **get_speaker(1332, {"begin_time": 300}),
            **get_speaker(
                1333,
                {"structure_level_list_of_speakers_id": 139, "speech_state": "contra"},
            ),
        },
        "structure_level_list_of_speakers": {
            # id_ = los_id * 10 + sl_id
            **get_sllos(111, {}),
            **get_sllos(112, {"speaker_ids": [1112, 1113]}),
            **get_sllos(113, {"speaker_ids": [1114]}),
            **get_sllos(211, {"speaker_ids": [2111, 2115, 2116]}),
            **get_sllos(311, {"speaker_ids": [3111]}),  # delete
            **get_sllos(512, {"speaker_ids": [5115]}),
            **get_sllos(125, {"speaker_ids": [1221]}),
            **get_sllos(126, {"speaker_ids": [1223]}),
            **get_sllos(139, {"speaker_ids": [1333]}),
        },
    }
    write(
        *[
            {"type": "create", "fqid": f"{collection}/{id_}", "fields": data}
            for collection, id_to_data in collection_to_id_to_data.items()
            for id_, data in id_to_data.items()
        ]
    )
    write(
        *[
            {
                "type": "delete",
                "fqid": fqid,
            }
            for fqid in to_delete
        ]
    )

    finalize("0071_remove_groupless_users")

    assert_model(
        "meeting/1",
        {
            **collection_to_id_to_data["meeting"][1],
            "speaker_ids": [1113, 5115],
            "meeting_user_ids": [13],
            "personal_note_ids": [],
        },
    )
    assert_model(
        "meeting/2",
        {
            **collection_to_id_to_data["meeting"][2],
            "speaker_ids": [],
            "meeting_user_ids": [],
            "personal_note_ids": [],
        },
    )
    assert_model(
        "meeting/3",
        {
            **collection_to_id_to_data["meeting"][3],
            "speaker_ids": [1331, 1332],
            "meeting_user_ids": [],
        },
    )
    assert_model(
        "meeting/4",
        {
            **collection_to_id_to_data["meeting"][4],
            "meta_deleted": True,
        },
    )

    assert_model(
        "group/1", {**collection_to_id_to_data["group"][1], "meeting_user_ids": [13]}
    )
    assert_model(
        "group/2", {**collection_to_id_to_data["group"][2], "meeting_user_ids": []}
    )
    assert_model(
        "group/3", {**collection_to_id_to_data["group"][3], "meeting_user_ids": []}
    )

    for id_ in range(1, 4):
        assert_model(
            f"projector_countdown/{id_}",
            collection_to_id_to_data["projector_countdown"][id_],
        )

    assert_model("user/1", {"username": "admin", "meeting_user_ids": []})
    assert_model("user/2", {"username": "bob", "meeting_user_ids": []})
    assert_model("user/3", {"username": "charlotte", "meeting_user_ids": [13]})
    assert_model("user/4", {"meta_deleted": True, "username": "DELETED"})
    assert_model("user/5", {"username": "elizabeth", "meeting_user_ids": []})
    assert_model("user/6", {"username": "george", "meeting_user_ids": []})

    assert_model(
        "meeting_user/11",
        {
            **collection_to_id_to_data["meeting_user"][11],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/12",
        {
            **collection_to_id_to_data["meeting_user"][12],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/13",
        {
            "user_id": 3,
            "group_ids": [1],
            "meeting_id": 1,
            "speaker_ids": [1113],
            "chat_message_ids": [],
            "structure_level_ids": [1, 2],
            "vote_delegations_from_ids": [],
            "supported_motion_ids": [11],
        },
    )
    assert_model(
        "meeting_user/14",
        {
            **collection_to_id_to_data["meeting_user"][14],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/15",
        {
            **collection_to_id_to_data["meeting_user"][15],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/16",
        {
            **collection_to_id_to_data["meeting_user"][16],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/21",
        {
            **collection_to_id_to_data["meeting_user"][21],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/22",
        {
            **collection_to_id_to_data["meeting_user"][22],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/23",
        {
            **collection_to_id_to_data["meeting_user"][23],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/25",
        {
            **collection_to_id_to_data["meeting_user"][25],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/31",
        {
            **collection_to_id_to_data["meeting_user"][31],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/32",
        {
            **collection_to_id_to_data["meeting_user"][32],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/33",
        {
            **collection_to_id_to_data["meeting_user"][33],
            "meta_deleted": True,
        },
    )
    assert_model(
        "meeting_user/41",
        {**collection_to_id_to_data["meeting_user"][41], "meta_deleted": True},
    )

    assert_model(
        "list_of_speakers/11",
        {
            **collection_to_id_to_data["list_of_speakers"][11],
            "speaker_ids": [1113],
        },
    )
    assert_model(
        "list_of_speakers/21",
        {
            **collection_to_id_to_data["list_of_speakers"][21],
            "speaker_ids": [],
        },
    )
    assert_model(
        "list_of_speakers/31",
        {
            **collection_to_id_to_data["list_of_speakers"][31],
            "speaker_ids": [],
        },
    )
    assert_model(
        "list_of_speakers/41",
        {
            **collection_to_id_to_data["list_of_speakers"][41],
            "meta_deleted": True,
        },
    )
    assert_model(
        "list_of_speakers/51",
        {
            **collection_to_id_to_data["list_of_speakers"][51],
            "speaker_ids": [5115],
        },
    )
    assert_model(
        "list_of_speakers/12",
        {
            **collection_to_id_to_data["list_of_speakers"][12],
            "speaker_ids": [],
        },
    )
    assert_model(
        "list_of_speakers/22",
        {
            **collection_to_id_to_data["list_of_speakers"][22],
            "speaker_ids": [],
        },
    )
    assert_model(
        "list_of_speakers/13",
        {
            **collection_to_id_to_data["list_of_speakers"][13],
            "speaker_ids": [1331, 1332],
        },
    )

    assert_model(
        "motion/11",
        {**collection_to_id_to_data["motion"][11], "supporter_meeting_user_ids": [13]},
    )
    assert_model(
        "motion/12",
        {**collection_to_id_to_data["motion"][12], "supporter_meeting_user_ids": []},
    )
    assert_model(
        "motion/13",
        {
            **collection_to_id_to_data["motion"][13],
            "personal_note_ids": [],
            "supporter_meeting_user_ids": [],
        },
    )
    assert_model(
        "motion/14",
        {
            **collection_to_id_to_data["motion"][14],
            "meta_deleted": True,
        },
    )
    assert_model("motion/15", {**collection_to_id_to_data["motion"][15]})
    assert_model(
        "motion/21",
        {
            **collection_to_id_to_data["motion"][21],
            "personal_note_ids": [],
        },
    )
    assert_model("motion/22", {**collection_to_id_to_data["motion"][22]})
    assert_model(
        "motion/31",
        {
            **collection_to_id_to_data["motion"][31],
        },
    )

    for id_ in range(1, 5):
        assert_model(
            f"personal_note/{id_}",
            {
                **collection_to_id_to_data["personal_note"][id_],
                "meta_deleted": True,
            },
        )

    assert_model("motion_editor/1", {"weight": 1, "motion_id": 11, "meeting_id": 1})
    assert_model("motion_editor/2", {"weight": 2, "motion_id": 11, "meeting_id": 1})
    assert_model("motion_editor/3", {"weight": 1, "motion_id": 31, "meeting_id": 3})
    assert_model(
        "motion_editor/4",
        {
            **collection_to_id_to_data["motion_editor"][4],
            "meta_deleted": True,
        },
    )

    assert_model(
        "motion_working_group_speaker/1",
        {"weight": 1, "motion_id": 11, "meeting_id": 1},
    )
    assert_model(
        "motion_working_group_speaker/2",
        {"weight": 2, "motion_id": 11, "meeting_id": 1},
    )
    assert_model(
        "motion_working_group_speaker/3",
        {"weight": 1, "motion_id": 31, "meeting_id": 3},
    )
    assert_model(
        "motion_working_group_speaker/4",
        {
            **collection_to_id_to_data["motion_working_group_speaker"][4],
            "meta_deleted": True,
        },
    )

    assert_model("motion_submitter/1", {"weight": 1, "motion_id": 11, "meeting_id": 1})
    assert_model("motion_submitter/2", {"weight": 2, "motion_id": 11, "meeting_id": 1})
    assert_model("motion_submitter/3", {"weight": 1, "motion_id": 31, "meeting_id": 3})
    assert_model(
        "motion_submitter/4",
        {
            **collection_to_id_to_data["motion_submitter"][4],
            "meta_deleted": True,
        },
    )

    assert_model("assignment_candidate/1", {"meeting_id": 3})
    assert_model("assignment_candidate/2", {"meeting_id": 3})
    assert_model("assignment_candidate/3", {"meeting_id": 3})
    assert_model(
        "assignment_candidate/4",
        {**collection_to_id_to_data["assignment_candidate"][4], "meta_deleted": True},
    )

    assert_model(
        "chat_message/1",
        {"content": "Hey, any of u up?", "created": 100, "meeting_id": 1},
    )
    assert_model(
        "chat_message/2",
        {"content": "I am, wazzup dude?", "created": 200, "meeting_id": 1},
    )
    assert_model(
        "chat_message/3",
        {
            "content": "Wanna go ditch tomorrows conference and go bar hopping?",
            "created": 300,
            "meeting_id": 1,
        },
    )
    assert_model(
        "chat_message/4",
        {
            "content": "Absolutely, ma man! Conf's gonna be hella boring anyway...",
            "created": 400,
            "meeting_id": 1,
        },
    )
    assert_model(
        "chat_message/5",
        {"content": "Yo guys, can I join in?", "created": 500, "meeting_id": 1},
    )
    assert_model(
        "chat_message/6",
        {
            "content": "Why u even asking, bro? Of course!",
            "created": 600,
            "meeting_id": 1,
        },
    )
    assert_model(
        "chat_message/7",
        {"content": "Totally rad, thx.", "created": 700, "meeting_id": 1},
    )
    assert_model(
        "chat_message/8",
        {
            **collection_to_id_to_data["chat_message"][8],
            "meta_deleted": True,
        },
    )
    assert_model(
        "chat_message/9",
        {
            "content": "Have fun everyone, I'll go to the conference and catch you up later.",
            "created": 1200,
            "meeting_id": 1,
        },
    )
    assert_model(
        "chat_message/10", {"content": "You da man!", "created": 1300, "meeting_id": 1}
    )

    assert_model(
        "structure_level/1",
        {
            **collection_to_id_to_data["structure_level"][1],
            "meeting_user_ids": [13],
        },
    )
    assert_model(
        "structure_level/2",
        {
            **collection_to_id_to_data["structure_level"][2],
            "meeting_user_ids": [13],
        },
    )
    assert_model(
        "structure_level/3",
        {
            **collection_to_id_to_data["structure_level"][3],
            "meeting_user_ids": [],
        },
    )
    assert_model(
        "structure_level/4",
        {
            **collection_to_id_to_data["structure_level"][4],
            "meta_deleted": True,
        },
    )
    for id_ in range(5, 10):
        assert_model(
            f"structure_level/{id_}",
            {
                **collection_to_id_to_data["structure_level"][id_],
                "meeting_user_ids": [],
            },
        )

    assert_model(
        "point_of_order_category/1",
        {
            **collection_to_id_to_data["point_of_order_category"][1],
            "speaker_ids": [1113],
        },
    )
    assert_model(
        "point_of_order_category/2",
        {**collection_to_id_to_data["point_of_order_category"][2], "speaker_ids": []},
    )
    assert_model(
        "point_of_order_category/3",
        {
            **collection_to_id_to_data["point_of_order_category"][3],
            "meta_deleted": True,
        },
    )

    for id_ in [
        1111,
        1112,
        1114,
        2111,
        2115,
        2116,
        3111,
        3116,
        4111,
        1221,
        1223,
        2221,
        1333,
    ]:
        assert_model(
            f"speaker/{id_}",
            {
                **collection_to_id_to_data["speaker"][id_],
                "meta_deleted": True,
            },
        )
    assert_model(
        "speaker/1113",
        collection_to_id_to_data["speaker"][1113],
    )
    assert_model(
        "speaker/5115",
        {
            "begin_time": 100,
            "meeting_id": 1,
            "pause_time": 200,
            "list_of_speakers_id": 51,
            "structure_level_list_of_speakers_id": 512,
        },
    )
    assert_model(
        "speaker/1331",
        {
            "end_time": 200,
            "begin_time": 100,
            "meeting_id": 3,
            "list_of_speakers_id": 13,
        },
    )
    assert_model(
        "speaker/1332", {"begin_time": 300, "meeting_id": 3, "list_of_speakers_id": 13}
    )

    assert_model(
        "structure_level_list_of_speakers/111",
        collection_to_id_to_data["structure_level_list_of_speakers"][111],
    )
    assert_model(
        "structure_level_list_of_speakers/112",
        {
            **collection_to_id_to_data["structure_level_list_of_speakers"][112],
            "speaker_ids": [1113],
        },
    )
    assert_model(
        "structure_level_list_of_speakers/113",
        {
            **collection_to_id_to_data["structure_level_list_of_speakers"][113],
            "speaker_ids": [],
        },
    )
    assert_model(
        "structure_level_list_of_speakers/211",
        {
            **collection_to_id_to_data["structure_level_list_of_speakers"][211],
            "speaker_ids": [],
        },
    )
    assert_model(
        "structure_level_list_of_speakers/311",
        {
            **collection_to_id_to_data["structure_level_list_of_speakers"][311],
            "meta_deleted": True,
        },
    )
    assert_model(
        "structure_level_list_of_speakers/512",
        {
            **collection_to_id_to_data["structure_level_list_of_speakers"][512],
            "speaker_ids": [5115],
        },
    )
    assert_model(
        "structure_level_list_of_speakers/125",
        {
            **collection_to_id_to_data["structure_level_list_of_speakers"][125],
            "speaker_ids": [],
        },
    )
    assert_model(
        "structure_level_list_of_speakers/126",
        {
            **collection_to_id_to_data["structure_level_list_of_speakers"][126],
            "speaker_ids": [],
        },
    )
    assert_model(
        "structure_level_list_of_speakers/139",
        {
            **collection_to_id_to_data["structure_level_list_of_speakers"][139],
            "speaker_ids": [],
        },
    )
