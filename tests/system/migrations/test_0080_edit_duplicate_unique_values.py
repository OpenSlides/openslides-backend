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
            err_str = "\n* ".join(expect_or_error)
            assert str(e) == f"Migration exception:\n* {err_str}"
    else:
        finalize("0080_edit_duplicate_unique_values")
        for collection, expect_data in expect_or_error.items():
            for id_, expect in expect_data.items():
                assert_model(f"{collection}/{id_}", expect)


def build_chat_group_test_data(with_problems: bool = False) -> TestData:
    setup_data: IterableData = {"chat_group": {}}
    expect_data: IterableData = {"chat_group": {}}
    setup_data["meeting"] = expect_data["meeting"] = {
        1: {"chat_group_ids": [1, 2, *([4, 6, 7, 8, 9, 10] if with_problems else [])]},
        2: {"chat_group_ids": [5, 11] if with_problems else []},
    }
    setup_data["chat_group"][1] = expect_data["chat_group"][1] = {
        "name": "unproblematic",
        "meeting_id": 1,
    }
    setup_data["chat_group"][2] = expect_data["chat_group"][2] = {
        "name": "faux problematic",
        "meeting_id": 1,
    }
    setup_data["chat_group"][3] = {"name": "faux problematic", "meeting_id": 1}
    expect_data["chat_group"][3] = {
        "name": "faux problematic",
        "meeting_id": 1,
        "meta_deleted": True,
    }
    if with_problems:
        setup_data["chat_group"][4] = expect_data["chat_group"][4] = {
            "name": "different meeting",
            "meeting_id": 1,
        }
        setup_data["chat_group"][5] = expect_data["chat_group"][5] = {
            "name": "different meeting",
            "meeting_id": 2,
        }
        setup_data["chat_group"][6] = expect_data["chat_group"][6] = setup_data[
            "chat_group"
        ][7] = setup_data["chat_group"][8] = setup_data["chat_group"][9] = {
            "name": "actual problem",
            "meeting_id": 1,
        }
        expect_data["chat_group"][7] = {"name": "actual problem (2)", "meeting_id": 1}
        expect_data["chat_group"][8] = {"name": "actual problem (4)", "meeting_id": 1}
        expect_data["chat_group"][9] = {"name": "actual problem (5)", "meeting_id": 1}
        setup_data["chat_group"][10] = expect_data["chat_group"][10] = {
            "name": "actual problem (3)",
            "meeting_id": 1,
        }
        setup_data["chat_group"][11] = {"name": "actual problem (3)", "meeting_id": 1}
        expect_data["chat_group"][11] = {
            "name": "actual problem (3) (2)",
            "meeting_id": 1,
        }
        setup_data["chat_group"][11] = expect_data["chat_group"][11] = {
            "name": "actual problem",
            "meeting_id": 2,
        }
    return setup_data, {"chat_group": [3]}, expect_data


def build_single_external_id_test_data(collection: str, fail: bool = False) -> TestData:
    setup_data: IterableData = {collection: {}}
    expect_data: IterableData = {collection: {}}
    setup_data[collection][1] = expect_data[collection][1] = {"external_id": "unique"}
    setup_data[collection][2] = expect_data[collection][2] = {
        "external_id": "now unique"
    }
    setup_data[collection][3] = {"external_id": "now unique"}
    expect_data[collection][3] = {"external_id": "now unique", "meta_deleted": True}
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


def test_chat_group_success(write, finalize, assert_model):
    do_test(write, finalize, assert_model, build_chat_group_test_data())


def test_chat_group_success_with_problems(write, finalize, assert_model):
    do_test(
        write, finalize, assert_model, build_chat_group_test_data(with_problems=True)
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


# # commented out bc they only test one unique field.
# def test_mediafile_success(write, finalize, assert_model):
#     do_test(
#         write,
#         finalize,
#         assert_model,
#         build_single_issue_numbering_test_data("mediafile", "token", add_empty=True),
#     )


# def test_mediafile_success_with_problems(write, finalize, assert_model):
#     do_test(
#         write,
#         finalize,
#         assert_model,
#         build_single_issue_numbering_test_data(
#             "mediafile", "token", add_empty=True, with_problems=True
#         ),
#     )


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


# TODO: Test the following:
# 'mediafile': [('token',), ('title', 'parent_id', 'owner_id')],
# 'motion_comment': [('motion_id', 'section_id')],
# 'motion_editor': [('meeting_user_id', 'motion_id')],
# 'motion_submitter': [('meeting_user_id', 'motion_id')],
# 'motion_supporter': [('meeting_user_id', 'motion_id')],
# 'motion_state': [('name', 'workflow_id')]
# 'motion_working_group_speaker': [('meeting_user_id', 'motion_id')],
# 'option': [('content_object_id', 'poll_id')],
# 'personal_note': [('meeting_user_id', 'content_object_id')],
# 'projector_countdown': [('title', 'meeting_id')],
# 'structure_level': [('name', 'meeting_id')],
# 'structure_level_list_of_speakers': [('meeting_id', 'structure_level_id', 'list_of_speakers_id')],
# 'user': [('username',), ('member_number',), ('saml_id',)],
# and test all together.
