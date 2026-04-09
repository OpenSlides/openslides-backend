from copy import deepcopy
from typing import Any

import pytest

from openslides_backend.migrations.exceptions import MigrationException

IterableData = dict[str, dict[int, dict[str, Any]]]
ErrorData = list[str]
# setup, ids_to_delete, error
TestData = tuple[IterableData, dict[str, list[int]], list[str] | IterableData]


def do_test(write, finalize, assert_model, test_data: TestData) -> None:
    setup, to_delete, expect_or_error = test_data
    write(
        *[
            {"type": "create", "fqid": f"{collection}/{id_}", "fields": data}
            for collection, setup_data in setup.items()
            for id_, data in setup_data.items()
        ]
    )
    if to_delete:
        write(
            *[
                {"type": "delete", "fqid": f"{collection}/{id_}"}
                for collection, delete_ids in to_delete.items()
                for id_ in delete_ids
            ]
        )
    if isinstance(expect_or_error, list):
        try:
            finalize("0080_edit_duplicate_unique_values")
            raise pytest.fail("Expected migration to fail. It didn't.")
        except MigrationException as e:
            err_str = "\n* ".join(sorted(expect_or_error))
            assert str(e) == f"Migration exception:\n* {err_str}"
    else:
        finalize("0080_edit_duplicate_unique_values")
        for collection, expect_data in expect_or_error.items():
            for id_, expect in expect_data.items():
                assert_model(f"{collection}/{id_}", expect)


def build_name_unique_with_test_data(
    name_field: str,
    collection: str,
    id_field: str,
    back_collection: str,
    back_id_field: str,
    with_problems: bool = False,
) -> TestData:
    setup_data: IterableData = {collection: {}}
    expect_data: IterableData = {collection: {}}
    setup_data[back_collection] = expect_data[back_collection] = {
        1: {back_id_field: [1, 2, *([4, 6, 7, 8, 9, 10, 11] if with_problems else [])]},
        2: {back_id_field: [5, 12, 13] if with_problems else []},
    }
    setup_data[collection][1] = expect_data[collection][1] = {
        name_field: "unproblematic",
        id_field: 1,
    }
    setup_data[collection][2] = expect_data[collection][2] = {
        name_field: "faux problematic",
        id_field: 1,
    }
    setup_data[collection][3] = {name_field: "faux problematic", id_field: 1}
    expect_data[collection][3] = {
        name_field: "faux problematic",
        id_field: 1,
        "meta_deleted": True,
    }
    if with_problems:
        setup_data[collection][4] = expect_data[collection][4] = {
            name_field: "different meeting",
            id_field: 1,
        }
        setup_data[collection][5] = expect_data[collection][5] = {
            name_field: "different meeting",
            id_field: 2,
        }
        setup_data[collection][6] = expect_data[collection][6] = setup_data[collection][
            7
        ] = setup_data[collection][8] = setup_data[collection][9] = {
            name_field: "actual problem",
            id_field: 1,
        }
        expect_data[collection][7] = {name_field: "actual problem (2)", id_field: 1}
        expect_data[collection][8] = {name_field: "actual problem (4)", id_field: 1}
        expect_data[collection][9] = {name_field: "actual problem (5)", id_field: 1}
        setup_data[collection][10] = expect_data[collection][10] = {
            name_field: "actual problem (3)",
            id_field: 1,
        }
        setup_data[collection][11] = {name_field: "actual problem (3)", id_field: 1}
        expect_data[collection][11] = {
            name_field: "actual problem (3) (2)",
            id_field: 1,
        }
        setup_data[collection][12] = expect_data[collection][12] = {
            name_field: "actual problem",
            id_field: 2,
        }
        setup_data[collection][13] = expect_data[collection][13] = {
            id_field: 2,
        }
    return setup_data, {collection: [3]}, expect_data


def build_single_external_id_test_data(collection: str, fail: bool = False) -> TestData:
    setup_data: IterableData = {collection: {}}
    expect_data: IterableData = {collection: {}}
    setup_data[collection][1] = expect_data[collection][1] = {"external_id": "unique"}
    setup_data[collection][2] = expect_data[collection][2] = {
        "external_id": "now unique"
    }
    setup_data[collection][3] = {"external_id": "now unique"}
    expect_data[collection][3] = {"external_id": "now unique", "meta_deleted": True}
    setup_data[collection][6] = expect_data[collection][6] = {"id": 6}
    if fail:
        setup_data[collection][4] = {"external_id": "not unique"}
        setup_data[collection][5] = {"external_id": "not unique"}
        return (
            setup_data,
            {collection: [3]},
            [
                f"For collection {collection}: Ids [4, 5]: Duplicate values for ('external_id',) (values: ('not unique',)) cannot be handled."
            ],
        )
    return setup_data, {collection: [3]}, expect_data


def build_single_issue_numbering_test_data(
    collection: str, field: str, add_empty: bool = False, with_problems: bool = False
) -> TestData:
    setup_data: IterableData = {collection: {}}
    expect_data: IterableData = {collection: {}}
    setup_data[collection][1] = expect_data[collection][1] = {field: "train"}
    setup_data[collection][2] = expect_data[collection][2] = {field: "car"}
    setup_data[collection][3] = {
        field: "car",
    }
    expect_data[collection][3] = {field: "car", "meta_deleted": True}
    if with_problems:
        setup_data[collection][6] = expect_data[collection][6] = setup_data[collection][
            7
        ] = setup_data[collection][8] = setup_data[collection][9] = {
            field: "attack helicopter",
        }
        expect_data[collection][7] = {field: "attack helicopter (2)"}
        expect_data[collection][8] = {field: "attack helicopter (4)"}
        expect_data[collection][9] = {field: "attack helicopter (5)"}
        setup_data[collection][10] = expect_data[collection][10] = {
            field: "attack helicopter (3)"
        }
        setup_data[collection][11] = {field: "attack helicopter (3)"}
        expect_data[collection][11] = {field: "attack helicopter (3) (2)"}
    if add_empty:
        setup_data[collection][12] = expect_data[collection][12] = {"id": 12}
    return setup_data, {collection: [3]}, expect_data


def build_mediafile_test_data(
    add_empty: bool = False, with_problems: bool = False
) -> TestData:
    data, to_delete, expect = build_single_issue_numbering_test_data(
        "mediafile", "token", add_empty, with_problems
    )
    assert not isinstance(expect, list)
    data["mediafile"][4] = expect["mediafile"][4] = {"title": "Train.png (2)"}
    data["mediafile"][5] = expect["mediafile"][5] = {"title": "Train.png (3)"}
    data["mediafile"] = {id_: file.copy() for id_, file in data["mediafile"].items()}
    expect["mediafile"] = {
        id_: file.copy() for id_, file in expect["mediafile"].items()
    }
    for id_ in data["mediafile"]:
        data["mediafile"][id_]["owner_id"] = expect["mediafile"][id_]["owner_id"] = (
            "organization/1"
        )
        data["mediafile"][id_]["id"] = expect["mediafile"][id_]["id"] = id_
        if id_ not in [1, 9]:
            data["mediafile"][id_]["parent_id"] = expect["mediafile"][id_][
                "parent_id"
            ] = 1
    data["mediafile"][1]["child_ids"] = expect["mediafile"][1]["child_ids"] = [
        id_
        for id_ in data["mediafile"]
        if id_ not in to_delete["mediafile"] and id_ not in [1, 9]
    ]
    data["organization"] = expect["organization"] = {
        1: {
            "mediafile_ids": [
                id_ for id_ in data["mediafile"] if id_ not in to_delete["mediafile"]
            ]
        }
    }
    data["mediafile"][1]["title"] = expect["mediafile"][1]["title"] = "Car.png"
    data["mediafile"][2]["title"] = expect["mediafile"][2]["title"] = data["mediafile"][
        3
    ]["title"] = expect["mediafile"][3]["title"] = "Train.png"
    if with_problems:
        data["mediafile"][4]["title"] = data["mediafile"][6]["title"] = data[
            "mediafile"
        ][7]["title"] = "Train.png"
        data["mediafile"][4]["child_ids"] = expect["mediafile"][4]["child_ids"] = [9]
        expect["mediafile"][6]["title"] = "Train.png (4)"
        expect["mediafile"][7]["title"] = "Train.png (6)"
        data["mediafile"][8]["title"] = expect["mediafile"][8]["title"] = (
            "Train.png (5)"
        )
        data["mediafile"][9]["title"] = expect["mediafile"][9]["title"] = "Train.png"
        data["mediafile"][9]["parent_id"] = expect["mediafile"][9]["parent_id"] = 4
        data["mediafile"][10]["title"] = expect["mediafile"][10]["title"] = (
            "Helicopter.png"
        )
        data["mediafile"][11]["title"] = expect["mediafile"][11]["title"] = (
            "SameAsMeeting.png"
        )
    data["meeting"] = expect["meeting"] = {
        1: {"mediafile_ids": [13, 14, 15, 16]},
        2: {"mediafile_ids": [17, 18, 19, 20, 21, 23]},
    }
    data["mediafile"][13] = expect["mediafile"][13] = {
        "owner_id": "meeting/1",
        "title": "I'm.png",
        "child_ids": [14, 15, 16],
    }
    data["mediafile"][14] = expect["mediafile"][14] = {
        "owner_id": "meeting/1",
        "title": "on.png",
        "parent_id": 13,
    }
    data["mediafile"][15] = expect["mediafile"][15] = {
        "owner_id": "meeting/1",
        "title": "a.png",
        "parent_id": 13,
    }
    data["mediafile"][16] = expect["mediafile"][16] = {
        "owner_id": "meeting/1",
        "title": "boat.png",
        "parent_id": 13,
    }
    data["mediafile"][17] = expect["mediafile"][17] = {
        "owner_id": "meeting/2",
        "title": "Everybody look at me.png",
        "child_ids": [18, 19, 20, 21, 23],
    }
    data["mediafile"][18] = expect["mediafile"][18] = {
        "owner_id": "meeting/2",
        "title": "'cause I'm sailing'.png",
        "parent_id": 17,
    }
    data["mediafile"][19] = expect["mediafile"][19] = {
        "owner_id": "meeting/2",
        "title": "on a.png",
        "parent_id": 17,
    }
    data["mediafile"][20] = expect["mediafile"][20] = {
        "owner_id": "meeting/2",
        "title": "boat.png",
        "parent_id": 17,
    }
    data["mediafile"][21] = expect["mediafile"][21] = {
        "owner_id": "meeting/2",
        "title": "SameAsMeeting.png",
        "parent_id": 17,
    }
    data["mediafile"][23] = expect["mediafile"][23] = {
        "owner_id": "meeting/2",
        "parent_id": 17,
    }
    if with_problems:
        data["meeting"][2]["mediafile_ids"].append(22)
        data["mediafile"][17]["child_ids"].append(22)
        data["mediafile"][22] = {
            "owner_id": "meeting/2",
            "title": "boat.png",
            "parent_id": 17,
        }
        expect["mediafile"][22] = {
            "owner_id": "meeting/2",
            "title": "boat.png (2)",
            "parent_id": 17,
        }
    return data, to_delete, expect


def build_meeting_id_and_string_field_test_data(
    collection: str, back_rel: str, str_field: str, fail: bool = False
) -> TestData:
    setup_data: IterableData = {collection: {}}
    expect_data: IterableData = {collection: {}}
    setup_data["meeting"] = expect_data["meeting"] = {
        1: {back_rel: [1, 2, *([4, 5] if fail else []), 6]},
        2: {back_rel: [7]},
    }
    setup_data[collection][1] = expect_data[collection][1] = {
        "name": "unproblematic",
        str_field: "unique",
        "meeting_id": 1,
    }
    setup_data[collection][2] = expect_data[collection][2] = {
        "name": "faux problematic",
        str_field: "now unique",
        "meeting_id": 1,
    }
    setup_data[collection][3] = {
        "name": "deleted",
        str_field: "now unique",
        "meeting_id": 1,
    }
    expect_data[collection][3] = {
        "name": "deleted",
        str_field: "now unique",
        "meta_deleted": True,
        "meeting_id": 1,
    }
    setup_data[collection][6] = expect_data[collection][6] = {
        "name": "different_meeting",
        str_field: "different_meeting",
        "meeting_id": 1,
    }
    setup_data[collection][7] = expect_data[collection][7] = {
        "name": "different_meeting",
        str_field: "now different_meeting",
        "meeting_id": 2,
    }
    if fail:
        setup_data[collection][4] = {
            "name": "actual problem",
            str_field: "not unique",
            "meeting_id": 1,
        }
        setup_data[collection][5] = {
            "name": "actual problem's brother",
            str_field: "not unique",
            "meeting_id": 1,
        }
        return (
            setup_data,
            {collection: [3]},
            [
                f"For collection {collection}: Ids [4, 5]: Duplicate values for ('meeting_id', '{str_field}') (values: (1, 'not unique')) cannot be handled."
            ],
        )
    return setup_data, {collection: [3]}, expect_data


def build_meeting_user_test_data(fail: bool = False) -> TestData:
    setup_data: IterableData = {"meeting_user": {}}
    expect_data: IterableData = {"meeting_user": {}}
    setup_data["meeting"] = expect_data["meeting"] = {
        1: {"meeting_user_ids": [1, 3, *([6, 7] if fail else [])]},
        2: {"meeting_user_ids": [2, 4]},
    }
    setup_data["user"] = expect_data["user"] = {
        1: {"meeting_user_ids": [1, 2, *([6] if fail else [])]},
        2: {"meeting_user_ids": [3, 4, *([7] if fail else [])]},
    }
    setup_data["meeting_user"][1] = expect_data["meeting_user"][1] = {
        "user_id": 1,
        "meeting_id": 1,
    }
    setup_data["meeting_user"][2] = expect_data["meeting_user"][2] = {
        "user_id": 1,
        "meeting_id": 2,
    }
    setup_data["meeting_user"][3] = expect_data["meeting_user"][3] = {
        "user_id": 2,
        "meeting_id": 1,
    }
    setup_data["meeting_user"][4] = expect_data["meeting_user"][4] = {
        "user_id": 2,
        "meeting_id": 2,
    }
    setup_data["meeting_user"][5] = {"user_id": 1, "meeting_id": 1}
    expect_data["meeting_user"][5] = {
        "user_id": 1,
        "meeting_id": 1,
        "meta_deleted": True,
    }
    if fail:
        setup_data["meeting_user"][6] = {"user_id": 1, "meeting_id": 1}
        setup_data["meeting_user"][7] = {"user_id": 2, "meeting_id": 1}
        return (
            setup_data,
            {"meeting_user": [5]},
            [
                "For collection meeting_user: Ids [1, 6]: Duplicate values for ('meeting_id', 'user_id') (values: (1, 1)) cannot be handled.",
                "For collection meeting_user: Ids [3, 7]: Duplicate values for ('meeting_id', 'user_id') (values: (1, 2)) cannot be handled.",
            ],
        )
    return setup_data, {"meeting_user": [5]}, expect_data


def build_motion_comment_test_data(with_problems: bool = False) -> TestData:
    setup_data: IterableData = {
        "motion_comment": {},
        "meeting": {
            1: {
                "motion_comment_ids": [
                    1,
                    2,
                    3,
                    4,
                    *([6, 7, 8] if with_problems else []),
                ]
            }
        },
    }
    expect_data: IterableData = {
        "motion_comment": {},
        "meeting": {1: {"motion_comment_ids": [1, 2, 3, 4]}},
    }
    setup_data["motion"] = {
        1: {"comment_ids": [1, 2, *([6] if with_problems else [])]},
        2: {"comment_ids": [3, 4, *([7, 8] if with_problems else [])]},
    }
    expect_data["motion"] = {
        1: {"comment_ids": [1, 2]},
        2: {"comment_ids": [3, 4]},
    }
    setup_data["motion_comment_section"] = {
        1: {"comment_ids": [1, 3, *([7] if with_problems else [])]},
        2: {"comment_ids": [2, 4, *([6, 8] if with_problems else [])]},
    }
    expect_data["motion_comment_section"] = {
        1: {"comment_ids": [1, 3]},
        2: {"comment_ids": [2, 4]},
    }
    setup_data["motion_comment"][1] = expect_data["motion_comment"][1] = {
        "motion_id": 1,
        "section_id": 1,
        "comment": "Now stand aside, worthy adversary!",
    }
    setup_data["motion_comment"][2] = expect_data["motion_comment"][2] = {
        "motion_id": 1,
        "section_id": 2,
        "comment": "'Tis but a scratch!",
    }
    setup_data["motion_comment"][3] = expect_data["motion_comment"][3] = {
        "motion_id": 2,
        "section_id": 1,
        "comment": "A scratch? Your arm's off!",
    }
    setup_data["motion_comment"][4] = expect_data["motion_comment"][4] = {
        "motion_id": 2,
        "section_id": 2,
        "comment": "No, it isn't.",
    }
    setup_data["motion_comment"][5] = {
        "motion_id": 1,
        "section_id": 1,
        "comment": "What's that then?",
    }
    expect_data["motion_comment"][5] = {
        **setup_data["motion_comment"][5],
        "meta_deleted": True,
    }
    if with_problems:
        setup_data["motion_comment"] = {
            id_: comment.copy() for id_, comment in setup_data["motion_comment"].items()
        }
        expect_data["motion_comment"] = {
            id_: comment.copy()
            for id_, comment in expect_data["motion_comment"].items()
        }
        setup_data["motion_comment"][6] = {
            "motion_id": 1,
            "section_id": 2,
            "comment": "I've had worse.",
        }
        expect_data["motion_comment"][2][
            "comment"
        ] = "'Tis but a scratch!\nI've had worse."
        setup_data["motion_comment"][7] = {
            "motion_id": 2,
            "section_id": 1,
            "comment": "You liar!",
        }
        expect_data["motion_comment"][3][
            "comment"
        ] = "A scratch? Your arm's off!\nYou liar!"
        setup_data["motion_comment"][8] = {
            "motion_id": 2,
            "section_id": 2,
            "comment": "Come on, you pansy!",
        }
        expect_data["motion_comment"][4][
            "comment"
        ] = "No, it isn't.\nCome on, you pansy!"
        for id_ in [6, 7, 8]:
            expect_data["motion_comment"][id_] = {
                **setup_data["motion_comment"][id_],
                "meta_deleted": True,
            }
    for id_ in setup_data["motion_comment"]:
        setup_data["motion_comment"][id_]["meeting_id"] = 1
        expect_data["motion_comment"][id_]["meeting_id"] = 1
    return setup_data, {"motion_comment": [5]}, expect_data


def build_motion_meeting_user_test_data(
    collection_base: str, has_weight: bool = False, with_problems: bool = False
) -> TestData:
    collection = f"motion_{collection_base}"
    setup_data: IterableData = {
        collection: {},
        "meeting": {1: {}},
        "meeting_user": {},
        "motion": {},
    }
    expect_data: IterableData = {
        collection: {},
        "meeting": {1: {}},
        "meeting_user": {},
        "motion": {},
    }
    for coll in ["meeting_user", "motion"]:
        setup_data["meeting"][1][f"{coll}_ids"] = expect_data["meeting"][1][
            f"{coll}_ids"
        ] = [11, 12]
        for id_ in range(11, 13):
            setup_data[coll][id_] = {"meeting_id": 1}
            expect_data[coll][id_] = {"meeting_id": 1}

    setup_data["meeting"][1][f"{collection}_ids"] = [1, 2, 3, 4]
    setup_data["motion"][11][f"{collection_base}_ids"] = [1, 3]
    setup_data["motion"][12][f"{collection_base}_ids"] = [2, 4]
    setup_data["meeting_user"][11][f"{collection}_ids"] = [1, 2]
    setup_data["meeting_user"][12][f"{collection}_ids"] = [3, 4]
    setup_data[collection][1] = expect_data[collection][1] = {
        "meeting_user_id": 11,
        "motion_id": 11,
    }
    setup_data[collection][2] = expect_data[collection][2] = {
        "meeting_user_id": 11,
        "motion_id": 12,
    }
    setup_data[collection][3] = expect_data[collection][3] = {
        "meeting_user_id": 12,
        "motion_id": 11,
    }
    setup_data[collection][4] = expect_data[collection][4] = {
        "meeting_user_id": 12,
        "motion_id": 12,
    }
    if with_problems:
        setup_data["meeting"][1][f"{collection}_ids"].extend([5, 6, 7])
        setup_data["motion"][11][f"{collection_base}_ids"].extend([5, 6, 7])
        setup_data["meeting_user"][11][f"{collection}_ids"].extend([5, 6])
        setup_data["meeting_user"][12][f"{collection}_ids"].extend([7])
        setup_data[collection][5] = expect_data[collection][5] = {
            "meeting_user_id": 11,
            "motion_id": 11,
        }
        setup_data[collection][6] = expect_data[collection][6] = {
            "meeting_user_id": 11,
            "motion_id": 11,
        }
        setup_data[collection][7] = expect_data[collection][7] = {
            "meeting_user_id": 12,
            "motion_id": 11,
        }
        expect_data[collection] = {
            id_: model.copy() for id_, model in expect_data[collection].items()
        }
        if has_weight:
            for id_ in [1, 3, 5]:
                expect_data[collection][id_]["meta_deleted"] = True
            expect_data["meeting"][1][f"{collection}_ids"] = [2, 4, 6, 7]
            expect_data["motion"][11][f"{collection_base}_ids"] = [6, 7]
            expect_data["motion"][12][f"{collection_base}_ids"] = [2, 4]
            expect_data["meeting_user"][11][f"{collection}_ids"] = [2, 6]
            expect_data["meeting_user"][12][f"{collection}_ids"] = [4, 7]
        else:
            for id_ in range(5, 8):
                expect_data[collection][id_]["meta_deleted"] = True
            expect_data["meeting"][1][f"{collection}_ids"] = [1, 2, 3, 4]
            expect_data["motion"][11][f"{collection_base}_ids"] = [1, 3]
            expect_data["motion"][12][f"{collection_base}_ids"] = [2, 4]
            expect_data["meeting_user"][11][f"{collection}_ids"] = [1, 2]
            expect_data["meeting_user"][12][f"{collection}_ids"] = [3, 4]
    else:
        for coll in ["meeting", "motion", "meeting_user"]:
            expect_data[coll] = setup_data[coll]
    setup_data[collection][8] = {
        "meeting_user_id": 12,
        "motion_id": 12,
    }
    expect_data[collection][8] = {
        "meeting_user_id": 12,
        "motion_id": 12,
        "meta_deleted": True,
    }
    for id_ in setup_data[collection]:
        setup_data[collection][id_]["meeting_id"] = expect_data[collection][id_][
            "meeting_id"
        ] = 1
        setup_data[collection][id_]["id"] = expect_data[collection][id_]["id"] = id_
        if has_weight:
            setup_data[collection][id_]["weight"] = expect_data[collection][id_][
                "weight"
            ] = (len(setup_data) - id_)
    return setup_data, {collection: [8]}, expect_data


def build_option_test_data(fail: bool = False) -> TestData:
    setup_data: IterableData = {"option": {}}
    expect_data: IterableData = {"option": {}}
    setup_data["poll"] = expect_data["poll"] = {
        1: {"option_ids": [1, 2, *([4, 5] if fail else []), 6]},
        2: {"option_ids": [7]},
    }
    setup_data["user"] = expect_data["user"] = {
        1: {"option_ids": [1]},
        2: {"option_ids": [2]},
        3: {"option_ids": [6]},
        4: {"option_ids": [7]},
        5: {"option_ids": [4, 5] if fail else []},
    }
    setup_data["option"][1] = expect_data["option"][1] = {
        "content_object_id": "user/1",
        "poll_id": 1,
    }
    setup_data["option"][2] = expect_data["option"][2] = {
        "content_object_id": "user/2",
        "poll_id": 1,
    }
    setup_data["option"][3] = {
        "content_object_id": "user/2",
        "poll_id": 1,
    }
    expect_data["option"][3] = {
        "content_object_id": "user/2",
        "meta_deleted": True,
        "poll_id": 1,
    }
    setup_data["option"][6] = expect_data["option"][6] = {
        "content_object_id": "user/3",
        "poll_id": 1,
    }
    setup_data["option"][7] = expect_data["option"][7] = {
        "content_object_id": "user/4",
        "poll_id": 2,
    }
    if fail:
        setup_data["option"][4] = {
            "content_object_id": "user/5",
            "poll_id": 1,
        }
        setup_data["option"][5] = {
            "content_object_id": "user/5",
            "poll_id": 1,
        }
        return (
            setup_data,
            {"option": [3]},
            [
                "For collection option: Ids [4, 5]: Duplicate values for ('content_object_id', 'poll_id') (values: ('user/5', 1)) cannot be handled."
            ],
        )
    return setup_data, {"option": [3]}, expect_data


def build_personal_note_test_data(with_problems: bool = False) -> TestData:
    setup_data: IterableData = {
        "personal_note": {},
        "meeting": {
            1: {
                "personal_note_ids": [1, 2, 3, 4, *([6, 7, 8] if with_problems else [])]
            }
        },
    }
    expect_data: IterableData = {
        "personal_note": {},
        "meeting": {1: {"personal_note_ids": [1, 2, 3, 4]}},
    }
    setup_data["motion"] = {
        1: {"personal_note_ids": [1, 2, *([6] if with_problems else [])]},
        2: {"personal_note_ids": [3, 4, *([7, 8] if with_problems else [])]},
    }
    expect_data["motion"] = {
        1: {"personal_note_ids": [1, 2]},
        2: {"personal_note_ids": [3, 4]},
    }
    setup_data["meeting_user"] = {
        21: {"personal_note_ids": [1, 3, *([7] if with_problems else [])]},
        22: {"personal_note_ids": [2, 4, *([6, 8] if with_problems else [])]},
    }
    expect_data["meeting_user"] = {
        21: {"personal_note_ids": [1, 3]},
        22: {"personal_note_ids": [2, 4]},
    }
    setup_data["personal_note"][1] = expect_data["personal_note"][1] = {
        "content_object_id": "motion/1",
        "meeting_user_id": 21,
        "note": "Now stand aside, worthy adversary!",
        "star": False,
    }
    setup_data["personal_note"][2] = expect_data["personal_note"][2] = {
        "content_object_id": "motion/1",
        "meeting_user_id": 22,
        "note": "'Tis but a scratch!",
        "star": True,
    }
    setup_data["personal_note"][3] = expect_data["personal_note"][3] = {
        "content_object_id": "motion/2",
        "meeting_user_id": 21,
        "note": "A scratch? Your arm's off!",
    }
    setup_data["personal_note"][4] = expect_data["personal_note"][4] = {
        "content_object_id": "motion/2",
        "meeting_user_id": 22,
        "note": "No, it isn't.",
        "star": False,
    }
    setup_data["personal_note"][5] = {
        "content_object_id": "motion/1",
        "meeting_user_id": 21,
        "note": "What's that then?",
        "star": True,
    }
    expect_data["personal_note"][5] = {
        **setup_data["personal_note"][5],
        "meta_deleted": True,
    }
    if with_problems:
        setup_data["personal_note"] = {
            id_: comment.copy() for id_, comment in setup_data["personal_note"].items()
        }
        expect_data["personal_note"] = {
            id_: comment.copy() for id_, comment in expect_data["personal_note"].items()
        }
        setup_data["personal_note"][6] = {
            "content_object_id": "motion/1",
            "meeting_user_id": 22,
            "note": "I've had worse.",
            "star": False,
        }
        expect_data["personal_note"][2]["note"] = "'Tis but a scratch!\nI've had worse."
        expect_data["personal_note"][2]["star"] = True
        setup_data["personal_note"][7] = {
            "content_object_id": "motion/2",
            "meeting_user_id": 21,
            "note": "You liar!",
            "star": True,
        }
        expect_data["personal_note"][3][
            "note"
        ] = "A scratch? Your arm's off!\nYou liar!"
        expect_data["personal_note"][3]["star"] = True
        setup_data["personal_note"][8] = {
            "content_object_id": "motion/2",
            "meeting_user_id": 22,
            "note": "Come on, you pansy!",
            "star": False,
        }
        expect_data["personal_note"][4]["note"] = "No, it isn't.\nCome on, you pansy!"
        expect_data["personal_note"][4]["star"] = False
        for id_ in [6, 7, 8]:
            expect_data["personal_note"][id_] = {
                **setup_data["personal_note"][id_],
                "meta_deleted": True,
            }
    for id_ in setup_data["personal_note"]:
        setup_data["personal_note"][id_]["meeting_id"] = 1
        expect_data["personal_note"][id_]["meeting_id"] = 1
    return setup_data, {"personal_note": [5]}, expect_data


def build_structure_level_list_of_speakers_test_data(fail: bool = False) -> TestData:
    setup_data: IterableData = {"structure_level_list_of_speakers": {}}
    expect_data: IterableData = {"structure_level_list_of_speakers": {}}
    setup_data["meeting"] = expect_data["meeting"] = {
        1: {
            "structure_level_list_of_speakers_ids": [
                1,
                3,
                *([6, 7] if fail else []),
                8,
                10,
            ]
        },
        2: {"structure_level_list_of_speakers_ids": [2, 4, 9, 11]},
    }
    setup_data["structure_level"] = expect_data["structure_level"] = {
        1: {
            "structure_level_list_of_speakers_ids": [1, 2, *([6] if fail else []), 8, 9]
        },
        2: {
            "structure_level_list_of_speakers_ids": [
                3,
                4,
                *([7] if fail else []),
                10,
                11,
            ]
        },
    }
    setup_data["list_of_speakers"] = expect_data["list_of_speakers"] = {
        1: {
            "structure_level_list_of_speakers_ids": [
                1,
                2,
                3,
                4,
                *([6, 7] if fail else []),
            ]
        },
        2: {"structure_level_list_of_speakers_ids": [8, 9, 10, 11]},
    }
    setup_data["structure_level_list_of_speakers"][1] = expect_data[
        "structure_level_list_of_speakers"
    ][1] = {"structure_level_id": 1, "meeting_id": 1, "list_of_speakers_id": 1}
    setup_data["structure_level_list_of_speakers"][2] = expect_data[
        "structure_level_list_of_speakers"
    ][2] = {"structure_level_id": 1, "meeting_id": 2, "list_of_speakers_id": 1}
    setup_data["structure_level_list_of_speakers"][3] = expect_data[
        "structure_level_list_of_speakers"
    ][3] = {"structure_level_id": 2, "meeting_id": 1, "list_of_speakers_id": 1}
    setup_data["structure_level_list_of_speakers"][4] = expect_data[
        "structure_level_list_of_speakers"
    ][4] = {"structure_level_id": 2, "meeting_id": 2, "list_of_speakers_id": 1}
    setup_data["structure_level_list_of_speakers"][8] = expect_data[
        "structure_level_list_of_speakers"
    ][8] = {"structure_level_id": 1, "meeting_id": 1, "list_of_speakers_id": 2}
    setup_data["structure_level_list_of_speakers"][9] = expect_data[
        "structure_level_list_of_speakers"
    ][9] = {"structure_level_id": 1, "meeting_id": 2, "list_of_speakers_id": 2}
    setup_data["structure_level_list_of_speakers"][10] = expect_data[
        "structure_level_list_of_speakers"
    ][10] = {"structure_level_id": 2, "meeting_id": 1, "list_of_speakers_id": 2}
    setup_data["structure_level_list_of_speakers"][11] = expect_data[
        "structure_level_list_of_speakers"
    ][11] = {"structure_level_id": 2, "meeting_id": 2, "list_of_speakers_id": 2}
    setup_data["structure_level_list_of_speakers"][5] = {
        "structure_level_id": 1,
        "meeting_id": 1,
        "list_of_speakers_id": 1,
    }
    expect_data["structure_level_list_of_speakers"][5] = {
        "structure_level_id": 1,
        "meeting_id": 1,
        "meta_deleted": True,
        "list_of_speakers_id": 1,
    }
    if fail:
        setup_data["structure_level_list_of_speakers"][6] = {
            "structure_level_id": 1,
            "meeting_id": 1,
            "list_of_speakers_id": 1,
        }
        setup_data["structure_level_list_of_speakers"][7] = {
            "structure_level_id": 2,
            "meeting_id": 1,
            "list_of_speakers_id": 1,
        }
        return (
            setup_data,
            {"structure_level_list_of_speakers": [5]},
            [
                "For collection structure_level_list_of_speakers: Ids [1, 6]: Duplicate values for ('meeting_id', 'structure_level_id', 'list_of_speakers_id') (values: (1, 1, 1)) cannot be handled.",
                "For collection structure_level_list_of_speakers: Ids [3, 7]: Duplicate values for ('meeting_id', 'structure_level_id', 'list_of_speakers_id') (values: (1, 2, 1)) cannot be handled.",
            ],
        )
    return setup_data, {"structure_level_list_of_speakers": [5]}, expect_data


def remove_none_values(model: dict[str, Any]) -> dict[str, Any]:
    return {key: val for key, val in model.items() if val is not None}


def build_user_test_data(fail: bool = False) -> TestData:
    setup_data: IterableData = {"user": {}}
    expect_data: IterableData = {"user": {}}
    test_data: list[tuple[str, str | None, str | None]] = [
        ("King Arthur", None, None),
        ("Sir Lancelot the Brave", "L4NC3L07", None),
        ("Sir Robin the-not-quite-so-brave-as-Sir-Lancelot", None, "Robin"),
        ("Sir Bedevere the Wise", "B3D3V323", "Bedevere"),
        ("Sir Galahad the Pure", "G4L4#4D", "Galahad"),
    ]
    for id_, (username, member_number, saml_id) in enumerate(test_data, 1):
        setup_data["user"][id_] = expect_data["user"][id_] = remove_none_values(
            {
                "username": username,
                "member_number": member_number,
                "saml_id": saml_id,
            }
        )
        setup_data["user"][id_ + 5] = expect_data["user"][id_] = remove_none_values(
            {
                "username": username,
                "member_number": member_number,
                "saml_id": saml_id,
            }
        )
    if fail:
        setup_data["user"][11] = remove_none_values(
            {
                "username": test_data[0][0],
                "member_number": "user11",
                "saml_id": "user11",
            }
        )
        setup_data["user"][12] = remove_none_values(
            {
                "username": "user12",
                "member_number": test_data[1][1],
                "saml_id": "user12",
            }
        )
        setup_data["user"][13] = remove_none_values(
            {
                "username": "user13",
                "member_number": "user13",
                "saml_id": test_data[2][2],
            }
        )
        setup_data["user"][14] = remove_none_values(
            {
                "username": test_data[3][0],
                "member_number": test_data[3][1],
                "saml_id": "user14",
            }
        )
        setup_data["user"][15] = remove_none_values(
            {
                "username": "user15",
                "member_number": test_data[4][1],
                "saml_id": test_data[4][2],
            }
        )
        setup_data["user"][16] = remove_none_values(
            {
                "username": test_data[0][0],
                "member_number": "user16",
                "saml_id": test_data[0][2],
            }
        )
        username, member_number, saml_id = test_data[1]
        setup_data["user"][17] = remove_none_values(
            {
                "username": username,
                "member_number": member_number,
                "saml_id": saml_id,
            }
        )
        return (
            setup_data,
            {"user": [6, 7, 8, 9, 10]},
            [
                "For collection user: Ids [1, 11, 16]: Duplicate values for ('username',) (values: ('King Arthur',)) cannot be handled.",
                # No screaming bc of member_number/saml_id for King arthur bc empty
                "For collection user: Ids [2, 12, 17]: Duplicate values for ('member_number',) (values: ('L4NC3L07',)) cannot be handled.",
                "For collection user: Ids [2, 17]: Duplicate values for ('username',) (values: ('Sir Lancelot the Brave',)) cannot be handled.",
                # No screaming bc of saml_id for Lancelot bc empty
                "For collection user: Ids [3, 13]: Duplicate values for ('saml_id',) (values: ('Robin',)) cannot be handled.",
                "For collection user: Ids [4, 14]: Duplicate values for ('username',) (values: ('Sir Bedevere the Wise',)) cannot be handled.",
                "For collection user: Ids [4, 14]: Duplicate values for ('member_number',) (values: ('B3D3V323',)) cannot be handled.",
                "For collection user: Ids [5, 15]: Duplicate values for ('member_number',) (values: ('G4L4#4D',)) cannot be handled.",
                "For collection user: Ids [5, 15]: Duplicate values for ('saml_id',) (values: ('Galahad',)) cannot be handled.",
            ],
        )
    return setup_data, {"user": [6, 7, 8, 9, 10]}, expect_data


def test_chat_group_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_name_unique_with_test_data(
            "name", "chat_group", "meeting_id", "meeting", "chat_group_ids"
        ),
    )


def test_chat_group_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_name_unique_with_test_data(
            "name",
            "chat_group",
            "meeting_id",
            "meeting",
            "chat_group_ids",
            with_problems=True,
        ),
    )


def test_committee_success(write, finalize, assert_model):
    do_test(
        write, finalize, assert_model, build_single_external_id_test_data("committee")
    )


def test_committee_error(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_single_external_id_test_data("committee", fail=True),
    )


def test_gender_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_single_issue_numbering_test_data("gender", "name"),
    )


def test_gender_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_single_issue_numbering_test_data("gender", "name", with_problems=True),
    )


def test_group_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_meeting_id_and_string_field_test_data(
            "group", "group_ids", "external_id"
        ),
    )


def test_group_error(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_meeting_id_and_string_field_test_data(
            "group", "group_ids", "external_id", fail=True
        ),
    )


# commented out bc they only test one unique field.
def test_mediafile_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_mediafile_test_data(add_empty=True),
    )


def test_mediafile_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_mediafile_test_data(add_empty=True, with_problems=True),
    )


def test_meeting_success(write, finalize, assert_model):
    do_test(
        write, finalize, assert_model, build_single_external_id_test_data("meeting")
    )


def test_meeting_error(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_single_external_id_test_data("meeting", fail=True),
    )


def test_meeting_user_success(write, finalize, assert_model):
    do_test(write, finalize, assert_model, build_meeting_user_test_data())


def test_meeting_user_error(write, finalize, assert_model):
    do_test(write, finalize, assert_model, build_meeting_user_test_data(fail=True))


def test_motion_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_meeting_id_and_string_field_test_data("motion", "motion_ids", "number"),
    )


def test_motion_error(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_meeting_id_and_string_field_test_data(
            "motion", "motion_ids", "number", fail=True
        ),
    )


def test_motion_comment_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_comment_test_data(),
    )


def test_motion_comment_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_comment_test_data(with_problems=True),
    )


def test_motion_editor_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_meeting_user_test_data("editor", has_weight=True),
    )


def test_motion_editor_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_meeting_user_test_data(
            "editor", has_weight=True, with_problems=True
        ),
    )


def test_motion_submitter_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_meeting_user_test_data("submitter", has_weight=True),
    )


def test_motion_submitter_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_meeting_user_test_data(
            "submitter", has_weight=True, with_problems=True
        ),
    )


def test_motion_supporter_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_meeting_user_test_data("supporter"),
    )


def test_motion_supporter_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_meeting_user_test_data("supporter", with_problems=True),
    )


def test_motion_state_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_name_unique_with_test_data(
            "name", "motion_state", "workflow_id", "motion_workflow", "state_ids"
        ),
    )


def test_motion_state_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_name_unique_with_test_data(
            "name",
            "motion_state",
            "workflow_id",
            "motion_workflow",
            "state_ids",
            with_problems=True,
        ),
    )


def test_motion_working_group_speaker_success_with_problems(
    write, finalize, assert_model
):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_meeting_user_test_data(
            "working_group_speaker", has_weight=True, with_problems=True
        ),
    )


def test_motion_working_group_speaker_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_motion_meeting_user_test_data("working_group_speaker"),
    )


def test_option_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_option_test_data(),
    )


def test_option_error(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_option_test_data(fail=True),
    )


def test_personal_note_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_personal_note_test_data(),
    )


def test_personal_note_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_personal_note_test_data(with_problems=True),
    )


def test_projector_countdown_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_name_unique_with_test_data(
            "title",
            "projector_countdown",
            "meeting_id",
            "meeting",
            "projector_countdown_ids",
        ),
    )


def test_projector_countdown_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_name_unique_with_test_data(
            "title",
            "projector_countdown",
            "meeting_id",
            "meeting",
            "projector_countdown_ids",
            with_problems=True,
        ),
    )


def test_structure_level_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_name_unique_with_test_data(
            "name", "structure_level", "meeting_id", "meeting", "structure_level_ids"
        ),
    )


def test_structure_level_success_with_problems(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_name_unique_with_test_data(
            "name",
            "structure_level",
            "meeting_id",
            "meeting",
            "structure_level_ids",
            with_problems=True,
        ),
    )


def test_structure_level_list_of_speakers_success(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_structure_level_list_of_speakers_test_data(),
    )


def test_structure_level_list_of_speakers_error(write, finalize, assert_model):
    do_test(
        write,
        finalize,
        assert_model,
        build_structure_level_list_of_speakers_test_data(fail=True),
    )


def test_user_success(write, finalize, assert_model):
    do_test(write, finalize, assert_model, build_user_test_data())


def test_user_error(write, finalize, assert_model):
    do_test(write, finalize, assert_model, build_user_test_data(fail=True))


def merge_iterable_data(data1: IterableData, data2: IterableData) -> None:
    data2 = {
        coll: {
            id_: {field: deepcopy(val) for field, val in model.items()}
            for id_, model in coll_data.items()
        }
        for coll, coll_data in data2.items()
    }
    for collection, models in data2.items():
        if collection not in data1:
            data1[collection] = models
        else:
            for id_, model in models.items():
                if id_ not in data1[collection]:
                    data1[collection][id_] = model
                else:
                    for field, val in model.items():
                        if (
                            field not in data1[collection][id_]
                            or (into := data1[collection][id_][field]) is None
                        ):
                            data1[collection][id_][field] = val
                        elif val is None:
                            pass
                        elif (
                            isinstance(into, str)
                            or isinstance(into, int)
                            or isinstance(into, bool)
                        ):
                            if into != val:
                                raise Exception(
                                    f"Cannot merge immutables: {collection}/{id_}/{field}: '{into}' '{val}'"
                                )
                        elif isinstance(into, list):
                            data1[collection][id_][field] = list(
                                {*data1[collection][id_][field], *val}
                            )
                        else:
                            raise Exception(
                                f"Type not implemented: {collection}/{id_}/{field}: '{into}' '{val}'"
                            )


def merge_test_data(test_data: list[TestData]) -> TestData:
    setup_data: IterableData = {}
    to_delete_data: dict[str, list[int]] = {}
    expect_data: list[str] | IterableData = {}
    expect_errors: bool = False

    for setup, to_delete, expect in test_data:
        merge_iterable_data(setup_data, setup)
        for collection, delete_list in to_delete.items():
            if already := to_delete_data.get(collection):
                to_delete_data[collection] = list({*already, *delete_list})
            else:
                to_delete_data[collection] = delete_list
        if isinstance(expect, list):
            if expect_errors:
                assert isinstance(expect_data, list)
                expect_data += expect
            else:
                expect_errors = True
                expect_data = expect
        else:
            if not expect_errors:
                assert isinstance(expect_data, dict)
                merge_iterable_data(expect_data, expect)
    return setup_data, to_delete_data, expect_data


def test_all_successes(write, finalize, assert_model) -> None:
    do_test(
        write,
        finalize,
        assert_model,
        merge_test_data(
            [
                build_name_unique_with_test_data(
                    "name", "chat_group", "meeting_id", "meeting", "chat_group_ids"
                ),
                build_single_external_id_test_data("committee"),
                build_single_issue_numbering_test_data("gender", "name"),
                build_meeting_id_and_string_field_test_data(
                    "group", "group_ids", "external_id"
                ),
                build_mediafile_test_data(add_empty=True),
                build_single_external_id_test_data("meeting"),
                build_meeting_user_test_data(),
                build_meeting_id_and_string_field_test_data(
                    "motion", "motion_ids", "number"
                ),
                build_motion_comment_test_data(),
                *[
                    build_motion_meeting_user_test_data(coll, has_weight=True)
                    for coll in ["editor", "submitter", "working_group_speaker"]
                ],
                build_motion_meeting_user_test_data("supporter"),
                build_name_unique_with_test_data(
                    "name",
                    "motion_state",
                    "workflow_id",
                    "motion_workflow",
                    "state_ids",
                ),
                build_option_test_data(),
                build_personal_note_test_data(),
                build_name_unique_with_test_data(
                    "title",
                    "projector_countdown",
                    "meeting_id",
                    "meeting",
                    "projector_countdown_ids",
                ),
                build_name_unique_with_test_data(
                    "name",
                    "structure_level",
                    "meeting_id",
                    "meeting",
                    "structure_level_ids",
                ),
                build_structure_level_list_of_speakers_test_data(),
                build_user_test_data(),
            ]
        ),
    )


def test_all_problems(write, finalize, assert_model) -> None:
    do_test(
        write,
        finalize,
        assert_model,
        merge_test_data(
            [
                build_name_unique_with_test_data(
                    "name",
                    "chat_group",
                    "meeting_id",
                    "meeting",
                    "chat_group_ids",
                    with_problems=True,
                ),
                build_single_external_id_test_data("committee"),
                build_single_issue_numbering_test_data(
                    "gender", "name", with_problems=True
                ),
                build_meeting_id_and_string_field_test_data(
                    "group", "group_ids", "external_id"
                ),
                build_mediafile_test_data(add_empty=True, with_problems=True),
                build_single_external_id_test_data("meeting"),
                build_meeting_user_test_data(),
                build_meeting_id_and_string_field_test_data(
                    "motion", "motion_ids", "number"
                ),
                build_motion_comment_test_data(with_problems=True),
                *[
                    build_motion_meeting_user_test_data(
                        coll, has_weight=True, with_problems=True
                    )
                    for coll in ["editor", "submitter", "working_group_speaker"]
                ],
                build_motion_meeting_user_test_data("supporter", with_problems=True),
                build_name_unique_with_test_data(
                    "name",
                    "motion_state",
                    "workflow_id",
                    "motion_workflow",
                    "state_ids",
                    with_problems=True,
                ),
                build_option_test_data(),
                build_personal_note_test_data(with_problems=True),
                build_name_unique_with_test_data(
                    "title",
                    "projector_countdown",
                    "meeting_id",
                    "meeting",
                    "projector_countdown_ids",
                    with_problems=True,
                ),
                build_name_unique_with_test_data(
                    "name",
                    "structure_level",
                    "meeting_id",
                    "meeting",
                    "structure_level_ids",
                    with_problems=True,
                ),
                build_structure_level_list_of_speakers_test_data(),
                build_user_test_data(),
            ]
        ),
    )


def test_all_failures(write, finalize, assert_model) -> None:
    do_test(
        write,
        finalize,
        assert_model,
        merge_test_data(
            [
                build_name_unique_with_test_data(
                    "name", "chat_group", "meeting_id", "meeting", "chat_group_ids"
                ),
                build_single_external_id_test_data("committee", fail=True),
                build_single_issue_numbering_test_data("gender", "name"),
                build_meeting_id_and_string_field_test_data(
                    "group", "group_ids", "external_id", fail=True
                ),
                build_mediafile_test_data(add_empty=True),
                build_single_external_id_test_data("meeting", fail=True),
                build_meeting_user_test_data(fail=True),
                build_meeting_id_and_string_field_test_data(
                    "motion", "motion_ids", "number", fail=True
                ),
                build_motion_comment_test_data(),
                *[
                    build_motion_meeting_user_test_data(coll, has_weight=True)
                    for coll in ["editor", "submitter", "working_group_speaker"]
                ],
                build_motion_meeting_user_test_data("supporter"),
                build_name_unique_with_test_data(
                    "name",
                    "motion_state",
                    "workflow_id",
                    "motion_workflow",
                    "state_ids",
                ),
                build_option_test_data(fail=True),
                build_personal_note_test_data(),
                build_name_unique_with_test_data(
                    "title",
                    "projector_countdown",
                    "meeting_id",
                    "meeting",
                    "projector_countdown_ids",
                ),
                build_name_unique_with_test_data(
                    "name",
                    "structure_level",
                    "meeting_id",
                    "meeting",
                    "structure_level_ids",
                ),
                build_structure_level_list_of_speakers_test_data(fail=True),
                build_user_test_data(fail=True),
            ]
        ),
    )
