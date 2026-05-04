import re
from collections import defaultdict
from typing import Any, cast

import pytest

from openslides_backend.migrations.exceptions import MigrationException
from openslides_backend.models.base import model_registry
from openslides_backend.models.fields import (
    BaseRelationField,
    GenericRelationField,
    GenericRelationListField,
)
from openslides_backend.shared.patterns import (
    collection_and_id_from_fqid,
    collection_from_fqid,
    fqfield_from_collection_and_id_and_field,
    fqid_from_collection_and_id,
    id_from_fqid,
)

# real_collections is necessary bc otherwise it'll list fake_models
# from generic tests so long as those have run before (ew)
real_collections: list[str] = [
    "organization",
    "user",
    "meeting_user",
    "gender",
    "organization_tag",
    "theme",
    "committee",
    "meeting",
    "structure_level",
    "group",
    "personal_note",
    "tag",
    "agenda_item",
    "list_of_speakers",
    "structure_level_list_of_speakers",
    "point_of_order_category",
    "speaker",
    "topic",
    "motion",
    "motion_submitter",
    "motion_supporter",
    "motion_editor",
    "motion_working_group_speaker",
    "motion_comment",
    "motion_comment_section",
    "motion_category",
    "motion_block",
    "motion_change_recommendation",
    "motion_state",
    "motion_workflow",
    "poll",
    "option",
    "vote",
    "assignment",
    "assignment_candidate",
    "poll_candidate_list",
    "poll_candidate",
    "mediafile",
    "meeting_mediafile",
    "projector",
    "projection",
    "projector_message",
    "projector_countdown",
    "chat_group",
    "chat_message",
    "action_worker",
    "import_preview",
    "history_position",
    "history_entry",
]
models: dict[str, dict[str, dict[str, Any]]] = {
    collection: {
        field.own_field_name: (
            {
                "to": cast(BaseRelationField, field).to,
                "equal_fields": cast(BaseRelationField, field).equal_fields,
                "is_relation": True,
                "is_generic": isinstance(field, GenericRelationField)
                or isinstance(field, GenericRelationListField),
                "is_list_relation": cast(BaseRelationField, field).is_list_field,
            }
            if hasattr(field, "to")
            else {"is_relation": False, "is_generic": False, "is_list_relation": False}
        )
        for field in model_registry[collection]().get_fields()
    }
    for collection in real_collections
}
collection_to_id: dict[str, int] = {
    "organization": 1,
    **{
        collection: i
        for i, collection in enumerate(
            sorted([coll for coll in models if coll not in ["_meta", "organization"]]),
            2,
        )
    },
}
collection_to_fqid: dict[str, str] = {
    collection: f"{collection}/{id_}" for collection, id_ in collection_to_id.items()
}


def get_base_data(
    break_eq_fields_for_fqids: list[str] = [],
) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str, list[str]]]]:
    create_data: dict[str, dict[str, Any]] = {
        fqid: {"id": collection_to_id[collection]}
        for collection, fqid in collection_to_fqid.items()
    }
    expect_errors_for: list[tuple[str, str, list[str]]] = []
    collection_to_eq_fields: dict[str, set[str]] = defaultdict(set)
    finished_combinations: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    for collection, fields in models.items():
        id_ = collection_to_id[collection]
        fqid = collection_to_fqid[collection]
        for field, field_def in fields.items():
            equal_fields = get_equal_fields(field_def)
            if (not field_def["is_relation"] or not equal_fields) and not (
                collection == "meeting" and field == "admin_group_id"
            ):
                continue
            back_collection_data = get_back_collection_field_data(field_def)
            for back_collection, back_field_data in back_collection_data.items():
                for back_field, back_field_def in back_field_data.items():
                    # Ensure no combination of collection_fields is handled twice
                    combination = cast(
                        tuple[tuple[str, str], tuple[str, str]],
                        tuple(
                            sorted([(collection, field), (back_collection, back_field)])
                        ),
                    )
                    if combination in finished_combinations:
                        continue
                    finished_combinations.add(combination)

                    # Calculate back-collection data
                    back_is_list, back_is_generic, back_id, back_fqid, back_val = (
                        get_relation_side_data(
                            back_collection,
                            back_field,
                            back_field_def,
                            fqid,
                            id_,
                            create_data,
                        )
                    )

                    # Calculate relevant equal_fields,
                    # ensure they can be filled in the collections later
                    full_eq_f = equal_fields.union(get_equal_fields(back_field_def))
                    collection_to_eq_fields[collection].update(full_eq_f)
                    collection_to_eq_fields[back_collection].update(full_eq_f)

                    # Calculate and write front-collection data
                    is_list, _, i, fqi, val = get_relation_side_data(
                        collection,
                        field,
                        field_def,
                        back_fqid,
                        back_id,
                        create_data,
                        back_collection,
                    )

                    # Re-calculate in case the id changed
                    back_val = fqi if back_is_generic else i

                    # Write collection data.
                    if not is_list:
                        create_data[fqi][field] = val
                    elif field not in create_data[fqi]:
                        create_data[fqi][field] = [val]
                    elif val not in create_data[fqi][field]:
                        create_data[fqi][field].append(val)
                    if not back_is_list:
                        create_data[back_fqid][back_field] = back_val
                    elif back_field not in create_data[back_fqid]:
                        create_data[back_fqid][back_field] = [back_val]
                    elif back_val not in create_data[back_fqid][back_field]:
                        create_data[back_fqid][back_field].append(back_val)

    # Fill all equal_fields for the collection for every generated fqids
    # Also fill fields needed to pass the datastore check
    created_fqids = sorted(create_data)
    while len(created_fqids):
        fqid = created_fqids.pop()
        model = create_data[fqid]
        collection, id_ = collection_and_id_from_fqid(fqid)
        eq_fields = collection_to_eq_fields[collection]
        for eq_field in eq_fields:
            created_fqids.extend(
                fill_field(
                    model,
                    collection,
                    eq_field,
                    id_,
                    create_data,
                    use_other_model=fqid in break_eq_fields_for_fqids,
                )
            )
        match collection:
            case "meeting_mediafile":
                fill_field(model, collection, "mediafile_id", id_, create_data)
                if ag_ids := model.get("access_group_ids"):
                    model["is_public"] = False
                    model["inherited_access_group_ids"] = ag_ids
                else:
                    model["is_public"] = True
                    model["inherited_access_group_ids"] = []
            case "group":
                if ag_ids := model["meeting_mediafile_access_group_ids"]:
                    model["meeting_mediafile_inherited_access_group_ids"] = ag_ids
    # Generate data for expected errors
    eq_fields_combinations: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for combinations in finished_combinations:
        eq_fields_combinations[combinations[0]][combinations[1][0]] = combinations[1][1]
        eq_fields_combinations[combinations[1]][combinations[0][0]] = combinations[0][1]
    for fqid in break_eq_fields_for_fqids:
        model = create_data[fqid]
        collection, id_ = collection_and_id_from_fqid(fqid)
        for field, val in model.items():
            if not (
                back_combinations := eq_fields_combinations.get((collection, field))
            ):
                continue
            field_def = models[collection][field]
            if isinstance(val, list):
                expect_errors_for.extend(
                    get_expected_errors_for_list(
                        collection,
                        id_,
                        field,
                        field_def,
                        model,
                        val,
                        back_combinations,
                        create_data,
                    )
                )
            elif error := get_expected_error_for_single(
                collection,
                id_,
                field,
                field_def,
                model,
                val,
                back_combinations,
                create_data,
            ):
                expect_errors_for.append(error)
    return create_data, expect_errors_for


def get_back_collection_field_data(
    field_def: dict[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    if field_def["is_generic"]:
        return {
            coll: {field: models[coll][field]}
            for coll, field in field_def["to"].items()
        }
    back_collection, back_field = list(field_def["to"].items())[0]
    back_field_def = models[back_collection][back_field]
    return {back_collection: {back_field: back_field_def}}


def get_equal_fields(field_def: dict[str, Any]) -> set[str]:
    if not (eq_fields := field_def.get("equal_fields")):
        return set()
    if isinstance(eq_fields, list):
        return set(eq_fields)
    return {eq_fields}


def get_relation_side_data(
    collection: str,
    field: str,
    field_def: dict[str, Any],
    back_fqid: str,
    back_id: int,
    create_data: dict[str, dict[str, Any]],
    check_back_collection: str = "",
) -> tuple[bool, bool, int, str, str | int]:
    """
    Calculates
    - whether the relation is a list relation
    - whether the relation is a generic relation
    - the id to which the relation_data should be written
    - the fqid that corresponds
    - the single value that needs to be written into the field
    Also creates new create_data-entires in case there is a necessity
    """
    is_list = field_def["is_list_relation"]
    is_generic = field_def["is_generic"]
    id_ = collection_to_id[collection]
    fqid = collection_to_fqid[collection]
    val = back_fqid if is_generic else back_id
    if is_list:
        if collection == check_back_collection and id_ == back_id:
            id_ += 1
            fqid = f"{collection}/{id_}"
            if fqid not in create_data:
                create_data[fqid] = {"id": id_}
    elif field not in create_data[fqid] and not (
        collection == check_back_collection and id_ == back_id
    ):
        create_data[fqid][field] = val
    else:
        while (collection == check_back_collection and id_ == back_id) or (
            field in create_data[fqid] and val != create_data[fqid][field]
        ):
            id_ += 1
            fqid = f"{collection}/{id_}"
            if collection == check_back_collection and id_ == back_id:
                id_ += 1
                fqid = f"{collection}/{id_}"
            if fqid not in create_data:
                create_data[fqid] = {"id": id_}
    return (is_list, is_generic, id_, fqid, val)


def get_expected_errors_for_list(
    collection: str,
    id_: int,
    field: str,
    field_def: dict[str, Any],
    model: dict[str, Any],
    val: list[str] | list[int],
    back_combinations: dict[str, str],
    create_data: dict[str, dict[str, Any]],
) -> list[tuple[str, str, list[str]]]:
    expect_errors_for: list[tuple[str, str, list[str]]] = []
    if isinstance(val, list):
        for sub_val in val:
            if error := get_expected_error_for_single(
                collection,
                id_,
                field,
                field_def,
                model,
                sub_val,
                back_combinations,
                create_data,
            ):
                expect_errors_for.append(error)
    return expect_errors_for


def get_expected_error_for_single(
    collection: str,
    id_: int,
    field: str,
    field_def: dict[str, Any],
    model: dict[str, Any],
    val: str | int,
    back_combinations: dict[str, str],
    create_data: dict[str, dict[str, Any]],
) -> None | tuple[str, str, list[str]]:
    if isinstance(val, str):
        back_fqid = val
        back_coll, back_id = collection_and_id_from_fqid(back_fqid)
        back_field = back_combinations[back_coll]
    else:
        assert isinstance(val, int)
        assert len(back_combinations) == 1
        back_id = val
        back_coll, back_field = list(back_combinations.items())[0]
        back_fqid = fqid_from_collection_and_id(back_coll, back_id)
    back_field_def = models[back_coll][back_field]
    back_model = create_data[back_fqid]
    merged_eq_fields = sorted(
        get_equal_fields(field_def).union(get_equal_fields(back_field_def))
    )
    if "user" in [collection, back_coll]:
        merged_eq_fields = [
            field for field in merged_eq_fields if field != "meeting_id"
        ]
    if len(merged_eq_fields):
        return (
            f"{fqfield_from_collection_and_id_and_field(collection, id_, field)}: {tuple(model[f] if not (collection =='meeting' and f =='meeting_id') else id_ for f in merged_eq_fields)}",
            f"{fqfield_from_collection_and_id_and_field(back_coll, back_id, back_field)}: {tuple(back_model[f] if not (back_coll =='meeting' and f =='meeting_id') else back_id for f in merged_eq_fields)}",
            merged_eq_fields,
        )


def fill_field(
    model: dict[str, Any],
    collection: str,
    field: str,
    id_: int,
    create_data: dict[str, dict[str, Any]],
    use_other_model: bool = False,
) -> list[str]:
    created_fqids = []
    if field in model or field not in models[collection]:
        return created_fqids
    field_def = models[collection][field]
    assert field_def["is_relation"] and not field_def["is_list_relation"]
    to_coll, to_field = list(field_def["to"].items())[0]
    to_field_def = models[to_coll][to_field]
    if not to_field_def["is_list_relation"] or to_field_def["is_generic"]:
        raise Exception(f"{to_coll}/{to_field} is not list relation")
    if use_other_model:
        to_id = collection_to_id[to_coll] + 1
        to_fqid = fqid_from_collection_and_id(to_coll, to_id)
        if to_fqid not in create_data:
            create_data[to_fqid] = {"id": to_id}
            created_fqids.append(to_fqid)
    else:
        to_fqid = collection_to_fqid[to_coll]
        to_id = collection_to_id[to_coll]
    to_model = create_data[to_fqid]
    to_val = (
        fqid_from_collection_and_id(collection, id_)
        if to_field_def["is_generic"]
        else id_
    )
    if to_field not in to_model:
        to_model[to_field] = [to_val]
    elif to_val not in to_model[to_field]:
        to_model[to_field].append(to_val)
    if field_def["is_generic"]:
        model[field] = to_fqid
    else:
        model[field] = to_id
    return created_fqids


def remove_one_relation_side(
    create_data: dict[str, dict[str, Any]], front: bool = True
) -> None:
    """
    Removes one side from each relation that
    1. has equal_fields
    2. is not an equal_field of any other relation
    """
    for fqid, model in create_data.items():
        collection, id_ = collection_and_id_from_fqid(fqid)
        for field in list(model):
            value = model[field]
            if not (field_def := models[collection][field]).get("equal_fields") or any(
                field == (eq := models[collection][f].get("equal_fields"))
                or (isinstance(eq, list) and field in eq)
                for f in list(model)
            ):
                continue
            if isinstance(value, list):
                for val in value:
                    remove_val_from_single(
                        fqid,
                        id_,
                        field,
                        field_def,
                        model,
                        val,
                        create_data,
                        front,
                        from_list=True,
                    )
            else:
                remove_val_from_single(
                    fqid, id_, field, field_def, model, value, create_data, front
                )


def remove_val_from_single(
    fqid: str,
    id_: int,
    field: str,
    field_def: dict[str, Any],
    model: dict[str, Any],
    val: str | int,
    create_data: dict[str, dict[str, Any]],
    front: bool,
    from_list: bool = False,
) -> None:
    if isinstance(val, int):
        back_id = val
        back_collection, back_field = list(field_def["to"].items())[0]
        back_fqid = fqid_from_collection_and_id(back_collection, back_id)
    else:
        assert isinstance(val, str)
        back_fqid = val
        back_collection, back_id = collection_and_id_from_fqid(val)
        back_field = field_def["to"][back_collection]
    back_def = models[back_collection][back_field]
    back_generic = back_def["is_generic"]
    back_model = create_data[back_fqid]
    if any(
        back_field == (eq := models[back_collection][f].get("equal_fields"))
        or (isinstance(eq, list) and back_field in eq)
        for f in list(back_model)
    ):
        return
    if back_val := back_model.get(back_field):
        if front:
            if from_list:
                model[field] = [v for v in model[field] if v == val]
            else:
                del model[field]
        elif back_def["is_list_relation"]:
            if back_generic:
                to_del_at_back = fqid
            else:
                to_del_at_back = id_
            if to_del_at_back in back_val:
                back_model[back_field] = [
                    v for v in back_model[back_field] if v != to_del_at_back
                ]
        else:
            del back_model[back_field]


def base_test_fn(
    write,
    finalize,
    assert_model,
    break_eq_fields_for_fqids: list[str] = [],
    incomplete: bool = False,
    front: bool = True,
) -> None:
    create_data, expected_errors = get_base_data(break_eq_fields_for_fqids)
    if incomplete:
        remove_one_relation_side(create_data, front)
    write(
        *[
            {"type": "create", "fqid": fqid, "fields": model}
            for fqid, model in create_data.items()
        ]
    )
    if expected_errors:
        try:
            finalize("0081_check_equal_fields")
            raise pytest.fail(
                f"Expected migration 81 to fail for changed fqids {break_eq_fields_for_fqids}. It didn't."
            )
        except MigrationException as e:
            err_str = "\n* ".join(
                sorted(
                    f"Detected different equal_fields: {' and '.join(sorted([error1, error2]))} for equal_fields {tuple(eq_fields)}"
                    for error1, error2, eq_fields in expected_errors
                )
            )
            assert e.message == f"Migration exception:\n* {err_str}"
    else:
        finalize("0081_check_equal_fields")
        for fqid, model in create_data.items():
            assert_model(fqid, model)


def test_so_called_migration_success(write, finalize, assert_model) -> None:
    base_test_fn(write, finalize, assert_model)


"""
test_cases with equal_fields mismatches for one model are all cases where...
- There are equal_fields relations
- It isn't the meeting (that'll need an extra test because get_base_data cannot generate a broken state for the projection relation)
- If the relations are supposed to be one-sidedly broken, it can't be for a model where there are no expected errors, bc the migration not failing will cause the test to crash at the database-check phase.
"""
test_cases = [
    (
        fqid,
        [False, True, True][i % 3] and bool(get_base_data([fqid])[1]),
        [True, True, False][i % 3],
    )
    for i, (fqid, model) in enumerate(get_base_data()[0].items())
    if ((len(model) > 1 or "id" not in model) and fqid != "meeting/16")
]


@pytest.mark.parametrize(
    "break_eq_fields_for_fqids,incomplete,front",
    [([fqid], incomplete, front) for fqid, incomplete, front in test_cases],
    ids=[
        f"{fqid}{'' if not incomplete else '_fronts_removed' if front else '_backs_removed'}"
        for fqid, incomplete, front in test_cases
    ],
)
def test_so_called_migration_failure(
    write,
    finalize,
    assert_model,
    break_eq_fields_for_fqids: list[str],
    incomplete: bool,
    front: bool,
) -> None:
    base_test_fn(
        write, finalize, assert_model, break_eq_fields_for_fqids, incomplete, front
    )


def test_so_called_migration_failure_meeting_16(write, finalize, assert_model) -> None:
    create_data = get_base_data()[0]
    fqid = "projection/100"
    create_data[fqid] = {"id": 100}
    fill_field(create_data[fqid], "projection", "meeting_id", 100, create_data)
    fill_field(
        create_data[fqid],
        "projection",
        "content_object_id",
        100,
        create_data,
        use_other_model=True,
    )
    other_fqid = create_data[fqid]["content_object_id"]
    fill_field(
        create_data[other_fqid],
        collection_from_fqid(other_fqid),
        "meeting_id",
        id_from_fqid(other_fqid),
        create_data,
        use_other_model=True,
    )
    write(
        *[
            {"type": "create", "fqid": fqid, "fields": model}
            for fqid, model in create_data.items()
        ]
    )
    try:
        finalize("0081_check_equal_fields")
        raise pytest.fail(
            "Expected migration 81 to fail for changed projection/100. It didn't."
        )
    except MigrationException as e:
        assert "Migration exception:\n* Detected different equal_fields: " in e.message
        assert "projection/100/content_object_id: (16,)" in e.message
        assert "/projection_ids: (17,)" in e.message


def test_so_called_migration_failure_everything_deleted(
    write, finalize, assert_model
) -> None:
    create_data = get_base_data()[0]
    fqid = "projection/100"
    create_data[fqid] = {"id": 100}
    fill_field(create_data[fqid], "projection", "meeting_id", 100, create_data)
    fill_field(
        create_data[fqid],
        "projection",
        "content_object_id",
        100,
        create_data,
        use_other_model=True,
    )
    write(
        *[
            {"type": "create", "fqid": fqid, "fields": model}
            for fqid, model in create_data.items()
        ]
    )
    write(*[{"type": "delete", "fqid": fqid} for fqid in create_data.keys()])
    finalize("0081_check_equal_fields")
    for fqid, model in create_data.items():
        assert_model(fqid, {**model, "meta_deleted": True})


def test_so_called_migration_failure_delete_only_meeting(
    write, finalize, assert_model
) -> None:
    create_data = get_base_data()[0]
    write(
        *[
            {"type": "create", "fqid": fqid, "fields": model}
            for fqid, model in create_data.items()
        ]
    )
    write({"type": "delete", "fqid": (fqid := collection_to_fqid["group"])})
    try:
        finalize("0081_check_equal_fields")
        raise pytest.fail(
            f"Expected migration 81 to fail for deleted {fqid}. It didn't."
        )
    except MigrationException as e:
        assert "Migration exception:\n* Detected different equal_fields: " in e.message
        assert f"{fqid}/" in e.message
        substrs = []
        for part in e.message.split(":"):
            if fqid in part:
                i = part.index(fqid)
                substrs.append(part[i:])
        assert sorted(substrs) == sorted(
            [
                "group/10/meeting_user_ids",
                "group/10/meeting_mediafile_access_group_ids",
                "group/10/read_comment_section_ids",
                "group/10/write_comment_section_ids",
                "group/10/read_chat_group_ids",
                "group/10/write_chat_group_ids",
                "group/10/poll_ids",
            ]
        )
        for substr in substrs:
            assert re.search(f".*{substr}: \\((None,)*(None,|None)\\) .*", e.message)
