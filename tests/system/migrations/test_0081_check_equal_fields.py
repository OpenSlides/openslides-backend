from collections import defaultdict
from typing import Any, cast

import pytest

from cli.util.util import open_yml_file
from openslides_backend.migrations.exceptions import MigrationException
from openslides_backend.shared.patterns import (
    collection_and_id_from_fqid,
    collection_from_collectionfield,
    field_from_collectionfield,
    fqfield_from_collection_and_id_and_field,
    fqid_from_collection_and_id,
)

models = open_yml_file("./meta/models.yml")
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


def get_back_collection_field_data(
    typ: str, field_def: dict[str, Any]
) -> dict[str, dict[str, dict[str, Any]]]:
    if typ.startswith("generic-"):
        if isinstance(field_def["to"], dict):
            back_field = field_def["to"]["field"]
            return {
                coll: {back_field: models[coll][back_field]}
                for coll in field_def["to"]["collections"]
            }
        collection_to_field = {
            collection_from_collectionfield(
                collectionfield
            ): field_from_collectionfield(collectionfield)
            for collectionfield in field_def["to"]
        }
        return {
            coll: {field: models[coll][field]}
            for coll, field in collection_to_field.items()
        }
    back_collection, back_field = field_def["to"].split("/")
    back_field_def = models[back_collection][back_field]
    return {back_collection: {back_field: back_field_def}}


def get_equal_fields(field_def: dict[str, Any]) -> set[str]:
    if not (eq_fields := field_def.get("equal_fields")):
        return set()
    if isinstance(eq_fields, list):
        return set(eq_fields)
    return {eq_fields}


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
        if collection == "_meta":
            continue
        id_ = collection_to_id[collection]
        fqid = collection_to_fqid[collection]
        for field, field_def in fields.items():
            typ: str = field_def["type"]
            if "relation" not in typ or not (
                equal_fields := get_equal_fields(field_def)
            ):
                continue
            back_collection_data = get_back_collection_field_data(typ, field_def)
            for back_collection, back_field_data in back_collection_data.items():
                for back_field, back_field_def in back_field_data.items():
                    combination = cast(
                        tuple[tuple[str, str], tuple[str, str]],
                        tuple(
                            sorted([(collection, field), (back_collection, back_field)])
                        ),
                    )
                    if combination in finished_combinations:
                        continue
                    back_typ: str = back_field_def["type"]
                    back_is_list = back_typ.endswith("-list")
                    back_is_generic = back_typ.startswith("generic-")
                    back_id = collection_to_id[back_collection]
                    back_fqid = collection_to_fqid[back_collection]
                    back_val = fqid if back_is_generic else id_
                    if not back_is_list:
                        while (
                            back_field in create_data[back_fqid]
                            and back_val != create_data[back_fqid][back_field]
                        ):
                            back_id += 1
                            back_fqid = f"{back_collection}/{back_id}"
                            back_val = fqid if back_is_generic else id_
                            if back_fqid not in create_data:
                                create_data[back_fqid] = {"id": back_id}
                    full_eq_f = equal_fields.union(get_equal_fields(back_field_def))
                    collection_to_eq_fields[collection].update(full_eq_f)
                    collection_to_eq_fields[back_collection].update(full_eq_f)
                    val = back_fqid if typ.startswith("generic-") else back_id
                    if typ.endswith("-list"):
                        fqi = fqid
                        if collection == back_collection and id_ == back_id:
                            i = id_ + 1
                            fqi = f"{collection}/{i}"
                            back_val = fqi if back_is_generic else i
                        if field not in create_data[fqi]:
                            create_data[fqi][field] = [val]
                        elif val not in create_data[fqid][field]:
                            create_data[fqi][field].append(val)
                    elif field not in create_data[fqid] and not (
                        collection == back_collection and id_ == back_id
                    ):
                        create_data[fqid][field] = val
                    elif (
                        collection == back_collection and id_ == back_id
                    ) or val != create_data[fqid][field]:
                        i = id_ + 1
                        fqi = f"{collection}/{i}"
                        done = False
                        while not done:
                            if collection == back_collection and i == back_id:
                                i += 1
                                fqi = f"{collection}/{i}"
                            if fqi not in create_data:
                                create_data[fqi] = {"id": i, field: val}
                                done = True
                            elif field not in create_data[fqi]:
                                create_data[fqi][field] = val
                                done = True
                            elif create_data[fqi][field] == val:
                                done = True
                            else:
                                i += 1
                                fqi = f"{collection}/{i}"
                            back_val = fqi if back_is_generic else i
                    if not back_is_list:
                        create_data[back_fqid][back_field] = back_val
                    elif back_field not in create_data[back_fqid]:
                        create_data[back_fqid][back_field] = [back_val]
                    elif back_val not in create_data[back_fqid][back_field]:
                        create_data[back_fqid][back_field].append(back_val)
                    finished_combinations.add(
                        cast(
                            tuple[tuple[str, str], tuple[str, str]],
                            tuple(
                                sorted(
                                    [(collection, field), (back_collection, back_field)]
                                )
                            ),
                        )
                    )
    for fqid in sorted(create_data):
        model = create_data[fqid]
        collection, id_ = collection_and_id_from_fqid(fqid)
        eq_fields = collection_to_eq_fields[collection]
        for eq_field in eq_fields:
            fill_field(
                model,
                collection,
                eq_field,
                id_,
                create_data,
                use_other_model=fqid in break_eq_fields_for_fqids,
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
                for sub_val in val:
                    if isinstance(sub_val, str):
                        back_fqid = sub_val
                        back_coll, back_id = collection_and_id_from_fqid(back_fqid)
                        back_field = back_combinations[back_coll]
                        back_field_def = models[back_coll][back_field]
                        back_model = create_data[back_fqid]
                        merged_eq_fields = sorted(
                            get_equal_fields(field_def).union(
                                get_equal_fields(back_field_def)
                            )
                        )
                        expect_errors_for.append(
                            (
                                f"{fqfield_from_collection_and_id_and_field(collection, id_, field)}: {tuple(model[f] for f in merged_eq_fields)}",
                                f"{fqfield_from_collection_and_id_and_field(back_coll, back_id, back_field)}: {tuple(back_model[f] for f in merged_eq_fields)}",
                                merged_eq_fields,
                            )
                        )
                    else:
                        assert isinstance(sub_val, int)
                        assert len(back_combinations) == 1
                        back_id = sub_val
                        back_coll, back_field = list(back_combinations.items())[0]
                        back_fqid = fqid_from_collection_and_id(back_coll, back_id)
                        back_field_def = models[back_coll][back_field]
                        back_model = create_data[back_fqid]
                        merged_eq_fields = sorted(
                            get_equal_fields(field_def).union(
                                get_equal_fields(back_field_def)
                            )
                        )
                        expect_errors_for.append(
                            (
                                f"{fqfield_from_collection_and_id_and_field(collection, id_, field)}: {tuple(model[f] for f in merged_eq_fields)}",
                                f"{fqfield_from_collection_and_id_and_field(back_coll, back_id, back_field)}: {tuple(back_model[f] for f in merged_eq_fields)}",
                                merged_eq_fields,
                            )
                        )
            elif isinstance(val, str):
                back_fqid = val
                back_coll, back_id = collection_and_id_from_fqid(back_fqid)
                back_field = back_combinations[back_coll]
                back_field_def = models[back_coll][back_field]
                back_model = create_data[back_fqid]
                merged_eq_fields = sorted(
                    get_equal_fields(field_def).union(get_equal_fields(back_field_def))
                )
                expect_errors_for.append(
                    (
                        f"{fqfield_from_collection_and_id_and_field(collection, id_, field)}: {tuple(model[f] for f in merged_eq_fields)}",
                        f"{fqfield_from_collection_and_id_and_field(back_coll, back_id, back_field)}: {tuple(back_model[f] for f in merged_eq_fields)}",
                        merged_eq_fields,
                    )
                )
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
                expect_errors_for.append(
                    (
                        f"{fqfield_from_collection_and_id_and_field(collection, id_, field)}: {tuple(model[f] for f in merged_eq_fields)}",
                        f"{fqfield_from_collection_and_id_and_field(back_coll, back_id, back_field)}: {tuple(back_model[f] for f in merged_eq_fields)}",
                        merged_eq_fields,
                    )
                )
    return create_data, expect_errors_for


def fill_field(
    model: dict[str, Any],
    collection: str,
    field: str,
    id_: int,
    create_data: dict[str, dict[str, Any]],
    use_other_model: bool = False,
) -> None:
    if field in model or field not in models[collection]:
        return
    field_def = models[collection][field]
    match (typ := field_def["type"]):
        case "relation":
            to_coll, to_field = field_def["to"].split("/")
            to_field_def = models[to_coll][to_field]
            to_typ: str = to_field_def["type"]
            if to_typ != "relation-list":
                raise Exception(f"{to_coll}/{to_field} is not list relation")
            if use_other_model:
                to_fqid = fqid_from_collection_and_id(
                    to_coll, collection_to_id[to_coll] + 1
                )
                to_id = collection_to_id[to_coll] + 1
                if to_fqid not in create_data:
                    create_data[to_fqid] = {"id": to_id}
            else:
                to_fqid = collection_to_fqid[to_coll]
                to_id = collection_to_id[to_coll]
            to_model = create_data[to_fqid]
            to_val = (
                fqid_from_collection_and_id(collection, id_)
                if to_typ.startswith("generic-")
                else id_
            )
            if to_field not in to_model:
                to_model[to_field] = [to_val]
            elif to_val not in to_model[to_field]:
                to_model[to_field].append(to_val)
            model[field] = to_id
        case "generic-relation":
            to = field_def["to"]
            if isinstance(to, list):
                to_coll, to_field = to[0].split("/")
            else:
                to_coll = to["collections"][0]
                to_field = to["field"]
            to_field_def = models[to_coll][to_field]
            to_typ: str = to_field_def["type"]
            if to_typ != "relation-list":
                raise Exception(f"{to_coll}/{to_field} is not list relation")
            if use_other_model:
                to_fqid = fqid_from_collection_and_id(
                    to_coll, (to_id := collection_to_id[to_coll]) + 1
                )
                if to_fqid not in create_data:
                    create_data[to_fqid] = {"id": to_id}
            else:
                to_fqid = collection_to_fqid[to_coll]
            to_model = create_data[to_fqid]
            to_val = (
                fqid_from_collection_and_id(collection, id_)
                if to_typ.startswith("generic-")
                else id_
            )
            if to_field not in to_model:
                to_model[to_field] = [to_val]
            elif to_val not in to_model[to_field]:
                to_model[to_field].append(to_val)
            model[field] = to_fqid
        case _:
            raise Exception(f"{collection}/{field}: Unhandled type {typ}")


def base_test_fn(
    write, finalize, assert_model, break_eq_fields_for_fqids: list[str] = []
) -> None:
    create_data, expected_errors = get_base_data(break_eq_fields_for_fqids)
    write(
        *[
            {"type": "create", "fqid": fqid, "fields": model}
            for fqid, model in create_data.items()
        ]
    )
    if expected_errors:
        try:
            finalize("0081_check_equal_fields")
            raise pytest.fail("Expected migration 81 to fail. It didn't.")
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


@pytest.mark.parametrize(
    "break_eq_fields_for_fqids",
    [
        [fqid]
        for fqid, model in get_base_data()[0].items()
        if len(model) > 1 or "id" not in model
    ],
)
def test_so_called_migration_failure(
    write, finalize, assert_model, break_eq_fields_for_fqids: list[str]
) -> None:
    base_test_fn(write, finalize, assert_model, break_eq_fields_for_fqids)
