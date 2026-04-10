from collections.abc import Callable
from typing import Any, Literal, cast
from unittest import mock

import pytest
import yaml
from psycopg.errors import RaiseException

from cli.generate_models import Attribute, Model
from meta.dev.src import helper_get_names
from openslides_backend.action.action import Action
from openslides_backend.models import fields
from openslides_backend.shared.typing import DeletedModel
from tests.patch_model_registry_helper import FakeModel, PatchModelRegistryMixin

from .base_generic import BaseGenericTestCase

RefValType = int | str | list[int] | list[str]

collection_a = "fake_model_ef_a"
collection_b = "fake_model_ef_b"
collection_c = "fake_model_ef_c"


def turn_relation(relation: str) -> str:
    type1, type2 = relation.split(":")
    return f"{type2}:{type1}"


grouped_check_relations: list[tuple[str, ...]] = [
    ("1r:1t", "1rR:1t"),
    ("1r:nt", "1r:ntR", "1rR:nt"),
    ("1r:nr", "1rR:nr"),
    ("1Gr:nr",),
    ("1Gr:nt", "1GrR:nt"),
    ("nt:nt", "nt:ntR"),
    ("nGt:nt",),
    ("1Gr:1tR", "1GrR:1tR", "1GrR:1t"),
]
turned_grouped_check_relations: list[tuple[str, ...]] = [
    (
        (*relations, turned_relation)
        if (turned_relation := turn_relation(relations[0])) != relations[0]
        else relations
    )
    for relations in grouped_check_relations
]
check_trigger_existence_relations: list[str] = [
    group[-1] for group in turned_grouped_check_relations
]

equal_field_relations: list[tuple[str, str]] = []
for group in turned_grouped_check_relations:
    for i, relation in enumerate(group):
        isRR = all("R" in val for val in relation.split(":"))
        equal_field = "a_number" if isRR or i % 2 == 0 else "meeting_id"
        equal_field_relations.append((equal_field, relation))
        if len(group) == 1 and i == 0 and not isRR:
            equal_field_relations.append(("meeting_id", group[0]))


def interpret_field_type(field_type: str) -> tuple[bool, bool, bool]:
    """
    Returns multiple, generic, reference
    """
    return "n" in field_type, "G" in field_type or "g" in field_type, "r" in field_type


def generate_collection_field_name(
    field_type: str, back: bool = False
) -> tuple[str, bool]:
    if back:
        name = "back"
    else:
        name = "to"
    if "1" in field_type or "one" in field_type:
        return name + "_id", False
    else:
        return name + "_ids", True


def generate_collection_field_def(
    name: str,
    field_type: str,
    multi: bool,
    back_coll: str,
    back_name: str,
    equal_field: str | None = None,
) -> str:
    buffer = "                "
    definition = f"{name}:\n{buffer}type: "
    if generic := "g" in field_type.lower():
        definition += "generic-"
    definition += "relation"
    if multi:
        definition += "-list"
    if "r" in field_type:
        definition += f"\n{buffer}reference:"
        if generic:
            definition += f"\n{buffer}- "
        else:
            definition += " "
        definition += back_coll
    if "R" in field_type or "q" in field_type:
        definition += f"\n{buffer}required: true"
    definition += f"\n{buffer}to:"
    if generic:
        definition += f"\n{buffer}- "
    else:
        definition += " "
    definition += f"{back_coll}/{back_name}"
    if equal_field:
        definition += f"\n{buffer}equal_fields: {equal_field}"
    return definition


def get_collection_name(rel_type: str, base_coll: str, equal_field: str) -> str:
    uscore_rel_type = (
        rel_type.replace(":", "_").replace("1", "one").replace("R", "q").lower()
    )
    return f"{base_coll[-1]}_{equal_field}_{uscore_rel_type}"


def generate_collection_field_defs(
    coll_name: str, back_coll_name: str, rel_type: str, equal_field: str
) -> tuple[str, str]:
    first, second = rel_type.split(":")
    coll_name = get_collection_name(rel_type, coll_name, equal_field)
    back_coll_name = get_collection_name(rel_type, back_coll_name, equal_field)
    first_name, first_multi = generate_collection_field_name(first)
    second_name, second_multi = generate_collection_field_name(second, True)
    first_def = generate_collection_field_def(
        first_name, first, first_multi, back_coll_name, second_name, equal_field
    )
    second_def = generate_collection_field_def(
        second_name, second, second_multi, coll_name, first_name
    )
    return first_def, second_def


def generate_collection_fields(
    coll_name1: str, coll_name2: str, equal_field_relations: list[tuple[str, str]]
) -> str:
    definition1 = f"""
    _meta:
        id_field: &id_field
            type: number
            restriction_mode: A
            constant: true
            required: true
    {collection_a}:
        fields:
            id: *id_field"""
    definition2 = ""
    for equal_field, rel_type in equal_field_relations:
        b_coll = get_collection_name(rel_type, collection_b, equal_field)
        c_coll = get_collection_name(rel_type, collection_c, equal_field)
        field_group_1, field_group_2 = generate_collection_field_defs(
            coll_name1, coll_name2, rel_type, equal_field
        )
        definition1 += f"""
            {b_coll}_id:
                type: relation
                to: {b_coll}/meeting_id
            {c_coll}_ids:
                type: relation-list
                to: {c_coll}/meeting_id
                reference: {c_coll}"""
        definition2 += f"""
    {b_coll}:
        fields:
            id: *id_field
            a_number:
                type: number
            meeting_id:
                type: relation
                constant: true
                to: {collection_a}/{b_coll}_id
                reference: {collection_a}
            {field_group_1}
    {c_coll}:
        fields:
            id: *id_field
            a_number:
                type: number
            meeting_id:
                type: relation
                constant: true
                to: {collection_a}/{c_coll}_ids
                reference: {collection_a}
            {field_group_2}"""
    return definition1 + definition2


class FakeModelEFA(FakeModel):
    collection = "fake_model_ef_a"
    verbose_name = "fake model for equal field check a"
    id = fields.IntegerField()

    b_id = fields.RelationField(
        to={"fake_model_ef_b": "meeting_id"}, is_view_field=True
    )
    c_ids = fields.RelationListField(
        to={"fake_model_ef_c": "meeting_id"}, is_view_field=True
    )


def BaseFakeModelFactory(
    coll: str,
    short_coll: str,
    a_back_ending: str,
    rel_type: str,
    equal_field: str,
    field_name_to_field: dict[str, fields.Field],
) -> tuple[type[FakeModel], str]:
    uscore_rel_type = (
        rel_type.replace(":", "_")
        .replace("1", "one")
        .replace("R", "q")
        .replace(":", "_")
        .lower()
    )
    back_rel = f"{short_coll}_{equal_field}_{uscore_rel_type}_{a_back_ending}"

    class BaseFakeModelX(FakeModel):
        collection = get_collection_name(rel_type, coll, equal_field)
        verbose_name = f"fake model for equal field {equal_field} check {short_coll} with {rel_type} relation"

        id = fields.IntegerField()

        meeting_id = fields.RelationField(to={collection_a: back_rel}, constant=True)
        a_number = fields.IntegerField()

    for field_name, field in field_name_to_field.items():
        setattr(BaseFakeModelX, field_name, field)
    return BaseFakeModelX, back_rel


def get_attr_helper(collection: str, field_name: str, attr_data: Attribute) -> Any:
    to_data = attr_data.to
    to = to_data.to if to_data else {}
    clazz: (
        type[fields.GenericRelationListField]
        | type[fields.RelationListField]
        | type[fields.GenericRelationField]
        | type[fields.RelationField]
    )
    match attr_data.type:
        case "generic-relation-list":
            clazz = fields.GenericRelationListField
        case "relation-list":
            clazz = fields.RelationListField
        case "generic-relation":
            clazz = fields.GenericRelationField
        case "relation":
            clazz = fields.RelationField
        case _:
            raise Exception("get_attr_helper shouldn't be called for non-relations.")
    field = clazz(
        to=to,
        is_view_field=attr_data.is_view_field,
        write_fields=attr_data.write_fields,
        is_primary=attr_data.is_primary,
        required=attr_data.required,
    )
    field.own_field_name = field_name
    field.own_collection = collection
    return field


class TestEqualFieldsCheck(PatchModelRegistryMixin, BaseGenericTestCase):
    yml = generate_collection_fields(collection_b, collection_c, equal_field_relations)

    # rel_type to equal_field to collection type class_type to class
    classes: dict[
        str,
        dict[
            str,
            dict[
                str,
                dict[
                    Literal["class", "create", "update", "delete"],
                    type[FakeModel] | type[Action],
                ],
            ],
        ],
    ] = {}

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        orig_build_models_yaml_content = helper_get_names.build_models_yaml_content
        helper_get_names.build_models_yaml_content = mock.Mock()
        helper_get_names.build_models_yaml_content.return_value = cls.yml.encode()
        loaded_yml: dict[str, dict[str, Any]] = yaml.safe_load(cls.yml)
        for equal_field, rel_type in equal_field_relations:
            if rel_type not in cls.classes:
                cls.classes[rel_type] = {}
            cls.build_model_class(loaded_yml, "b", rel_type, collection_b, equal_field)
            cls.build_model_class(loaded_yml, "c", rel_type, collection_c, equal_field)
        helper_get_names.build_models_yaml_content = orig_build_models_yaml_content

    @classmethod
    def build_model_class(
        cls,
        loaded_yml: dict[str, dict[str, Any]],
        coll_abbrev: Literal["b", "c"],
        rel_type: str,
        collection: str,
        equal_field: str,
    ) -> None:
        coll = get_collection_name(rel_type, collection, equal_field)
        ef_model = Model(coll, loaded_yml[coll]["fields"])
        field_name = generate_collection_field_name(
            rel_type.split(":")[0 if coll_abbrev == "b" else 1], coll_abbrev == "c"
        )[0]
        ef_attr = ef_model.attributes[field_name]
        clas, back_rel = BaseFakeModelFactory(
            collection,
            coll_abbrev,
            "id" if coll_abbrev == "b" else "ids",
            rel_type,
            equal_field,
            {field_name: get_attr_helper(coll, field_name, ef_attr)},
        )
        setattr(
            FakeModelEFA,
            back_rel,
            fields.RelationListField(
                to={clas.collection: "meeting_id"}, is_view_field=True
            ),
        )
        if equal_field not in cls.classes[rel_type]:
            cls.classes[rel_type][equal_field] = {}
        cls.classes[rel_type][equal_field][collection] = {"class": clas}

    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                f"{collection_a}/1": {},
                f"{collection_a}/4": {},
            }
        )

    def get_reference_value(
        self, val: int, multiple: bool, generic: bool, target_coll: str
    ) -> RefValType:
        if generic:
            return_val: str | int = f"{target_coll}/{val}"
            if multiple:
                return [cast(str, return_val)]
        else:
            return_val = val
            if multiple:
                return [cast(int, return_val)]
        return return_val

    def get_test_relation_data(
        self, rel_type: str, equal_field: str
    ) -> tuple[str, str, RefValType, str, str, RefValType]:
        field1_type, field2_type = rel_type.split(":")
        multiple1, generic1, _ = interpret_field_type(field1_type)
        multiple2, generic2, _ = interpret_field_type(field2_type)
        field1, _ = generate_collection_field_name(field1_type)
        field2, _ = generate_collection_field_name(field2_type, True)
        b_coll = get_collection_name(rel_type, collection_b, equal_field)
        c_coll = get_collection_name(rel_type, collection_c, equal_field)
        ref_val1 = self.get_reference_value(1, multiple1, generic1, c_coll)
        ref_val2 = self.get_reference_value(1, multiple2, generic2, b_coll)
        return b_coll, field1, ref_val1, c_coll, field2, ref_val2

    def get_test_data(
        self,
        rel_type: str,
        equal_field: str,
        back: bool,
        fail: bool = False,
        is_update: bool = False,
    ) -> tuple[
        dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]
    ]:
        collection_b, field1, ref_val1, collection_c, field2, ref_val2 = (
            self.get_test_relation_data(rel_type, equal_field)
        )
        test_coll = collection_c if back else collection_b
        back_coll = collection_b if back else collection_c
        setup_data = {
            f"{back_coll}/1": {
                "meeting_id": 1,
                equal_field: 1,
            }
        }
        test_data = {
            f"{collection_b}/1": {field1: ref_val1},
            f"{collection_c}/1": {field2: ref_val2},
        }
        if is_update:
            setup_data[f"{test_coll}/1"] = {
                "meeting_id": 1,
                equal_field: 4 if fail else 1,
            }
        else:
            test_data[f"{test_coll}/1"].update(
                {
                    "meeting_id": 1,
                    equal_field: 4 if fail else 1,
                }
            )
        return (
            setup_data,
            test_data,
            {
                fqid: {**setup_data.get(fqid, {}), **date}
                for fqid, date in test_data.items()
            },
        )

    @classmethod
    def get_base_test_create_success_fn(
        cls, rel_type: str, equal_field: str, back: bool = False
    ) -> Callable:
        def base_test_success(self: TestEqualFieldsCheck) -> None:
            setup_data, test_data, expected = self.get_test_data(
                rel_type, equal_field, back
            )
            self.set_models(setup_data)
            try:
                self.set_models(test_data)
            except Exception as e:
                raise pytest.fail(str(e))
            for fqid, date in expected.items():
                self.assert_model_exists(fqid, date)

        return base_test_success

    @classmethod
    def get_base_test_update_success_fn(
        cls, rel_type: str, equal_field: str, back: bool = False
    ) -> Callable:
        def base_test_success(self: TestEqualFieldsCheck) -> None:
            setup_data, test_data, expected = self.get_test_data(
                rel_type, equal_field, back, is_update=True
            )
            self.set_models(setup_data)
            try:
                self.set_models(test_data)
            except Exception as e:
                raise pytest.fail(str(e))
            for fqid, date in expected.items():
                self.assert_model_exists(fqid, date)

        return base_test_success

    def assert_fail_test_error(
        self,
        response: str,
        equal_field: str,
        back: bool,
        field1: str,
        field2: str,
        collection_b: str,
        collection_c: str,
    ) -> None:
        shortened = response.split("\nCONTEXT:")[0]
        if equal_field == "meeting_id":
            if "to meeting 4:" in shortened:
                self.assertEqual(
                    f"The following models do not belong to meeting 4: ['{collection_b if back else collection_c}/1']",
                    shortened,
                )
            else:
                self.assertEqual(
                    f"The following models do not belong to meeting 1: ['{collection_c if back else collection_b}/1']",
                    shortened,
                )
        else:
            expect_field = field1 if field1 in shortened else field2
            for coll in [collection_b, collection_c]:
                if (generic_relation_name := f"{expect_field}_{coll}_id") in shortened:
                    expect_field = generic_relation_name
            self.assertIn(
                f"The relation {expect_field} requires the following fields to be equal:",
                shortened,
            )
            self.assertIn(
                f"\n {collection_b if back else collection_c}/1/a_number: 1", shortened
            )
            self.assertIn(
                f"\n {collection_c if back else collection_b}/1/a_number: 4", shortened
            )

    @classmethod
    def get_base_test_create_fail_fn(
        cls, rel_type: str, equal_field: str, back: bool = False
    ) -> Callable:
        def base_test_fail(self: TestEqualFieldsCheck) -> None:
            setup_data, test_data, _ = self.get_test_data(
                rel_type, equal_field, back, fail=True
            )
            self.set_models(setup_data)
            with pytest.raises(RaiseException) as e:
                self.set_models(test_data)
            collection_b, field1, _, collection_c, field2, _ = (
                self.get_test_relation_data(rel_type, equal_field)
            )
            self.assert_fail_test_error(
                str(e.value),
                equal_field,
                back,
                field1,
                field2,
                collection_b,
                collection_c,
            )

        return base_test_fail

    @classmethod
    def get_base_test_update_fail_fn(
        cls, rel_type: str, equal_field: str, back: bool = False
    ) -> Callable:
        def base_test_fail(self: TestEqualFieldsCheck) -> None:
            setup_data, test_data, _ = self.get_test_data(
                rel_type, equal_field, back, fail=True, is_update=True
            )
            self.set_models(setup_data)
            with pytest.raises(RaiseException) as e:
                self.set_models(test_data)
            collection_b, field1, _, collection_c, field2, _ = (
                self.get_test_relation_data(rel_type, equal_field)
            )
            self.assert_fail_test_error(
                str(e.value),
                equal_field,
                back,
                field1,
                field2,
                collection_b,
                collection_c,
            )

        return base_test_fail

    @classmethod
    def get_base_test_delete_fn(
        cls, rel_type: str, equal_field: str, back: bool = False
    ) -> Callable:
        def base_test_delete(self: TestEqualFieldsCheck) -> None:
            _, _, setup_data = self.get_test_data(rel_type, equal_field, back)
            collection_b, field1, ref_val1, collection_c, field2, ref_val2 = (
                self.get_test_relation_data(rel_type, equal_field)
            )
            self.set_models(setup_data)

            fqid = f"{collection_c if back else collection_b}/1"
            sides = rel_type.split(":")
            side = sides[0] if back else sides[1]
            needs_back_update = "1" in side and "r" in side
            try:
                self.set_models(
                    {
                        **(
                            {
                                f"{collection_b if back else collection_c}/1": {
                                    field1 if back else field2: None
                                }
                            }
                            if needs_back_update
                            else {}
                        ),
                        fqid: DeletedModel(),
                    }
                )
                self.adjust_id_sequences()
            except Exception as e:
                raise pytest.fail(str(e))
            self.assert_model_not_exists(fqid)

        return base_test_delete

    @classmethod
    def get_base_test_update_equal_field_success_fn(
        cls, rel_type: str, equal_field: str
    ) -> Callable:
        def base_test_update_equal_field(self: TestEqualFieldsCheck) -> None:
            _, _, setup_data = self.get_test_data(rel_type, equal_field, False)
            collection_b, _, _, collection_c, _, _ = self.get_test_relation_data(
                rel_type, equal_field
            )
            self.set_models(setup_data)
            try:
                self.set_models(
                    {
                        f"{collection_b}/1": {equal_field: 4},
                        f"{collection_c}/1": {equal_field: 4},
                    }
                )
            except Exception as e:
                raise pytest.fail(str(e))
            for coll in [collection_b, collection_c]:
                self.assert_model_exists(f"{coll}/1", {equal_field: 4})

        return base_test_update_equal_field

    @classmethod
    def get_base_test_update_equal_field_error_fn(
        cls, rel_type: str, equal_field: str, back: bool = False
    ) -> Callable:
        def base_test_update_equal_field(self: TestEqualFieldsCheck) -> None:
            _, _, setup_data = self.get_test_data(rel_type, equal_field, False)
            collection_b, field1, _, collection_c, field2, _ = (
                self.get_test_relation_data(rel_type, equal_field)
            )
            self.set_models(setup_data)
            with pytest.raises(RaiseException) as e:
                self.set_models(
                    {
                        f"{collection_c if back else collection_b}/1": {
                            "id": 1,
                            equal_field: 4,
                        }
                    }
                )
            self.assert_fail_test_error(
                str(e.value),
                equal_field,
                back,
                field1,
                field2,
                collection_b,
                collection_c,
            )

        return base_test_update_equal_field


def get_rr_stat(rel: str) -> list[bool]:
    return ["R" in val for val in rel.split(":")]


# This code attempts to remove any unnecessary test cases
# What is considered necessary?
# At least one (error) test per type of relation.
# All tests that are possible per group of relation
rel_to_tasks: dict[str, dict[str, bool]] = {}
for group in grouped_check_relations:
    rel_to_rr_stat = {rel: get_rr_stat(rel) for rel in group}
    # per relation in group, calculate possible test cases based on required values
    task_to_rel = {
        "back": [rel for rel, rr in rel_to_rr_stat.items() if not rr[0]],
        "to": [rel for rel, rr in rel_to_rr_stat.items() if not rr[1]],
        "update": [rel for rel, rr in rel_to_rr_stat.items() if not any(rr)],
    }
    unused = {rel for rel in group}
    # make sure the check_equal-field-update test is done for every relation
    # that is to be tested with the `a_number` field.
    for rel in group:
        if ("a_number", rel) in equal_field_relations:
            unused.remove(rel)
            rel_to_tasks[rel] = {"eq_update": True}
    # assign one relation of the group to each main test case if possible
    # try to always use one that hasn't been used for any other test type before.
    tasks = ["back", "to", "update"]
    for task in tasks:
        if allowed := task_to_rel[task]:
            if unused_allowed := sorted(unused.intersection(allowed)):
                unused.remove(unused_allowed[0])
                rel_to_tasks[unused_allowed[0]] = {task: True}
            else:
                rel_to_tasks[allowed[0]][task] = True
    # assign remaining relations of the group to whatever test type, making sure they are only tested once.
    for i, rel in enumerate(sorted(unused)):
        for j in range(3):
            task = tasks[(i + j) % len(tasks)]
            if rel in task_to_rel[task]:
                rel_to_tasks[rel] = {task: False}
                break
        if rel not in rel_to_tasks:
            rel_to_tasks[rel] = {"eq_update": False}
# One test for each relation type that checks if the trigger gets generated
# if equal_fields is on the other side
for rel in check_trigger_existence_relations:
    rr_stat = get_rr_stat(rel)
    if ("a_number", rel) in equal_field_relations:
        rel_to_tasks[rel] = {"eq_update": False}
    if not rr_stat[0]:
        rel_to_tasks[rel] = {"back": False}
    else:
        rel_to_tasks[rel] = {"to": False}

# This code adds the test functions for the selected cases to the test class
for equal_field, rel_type in equal_field_relations:
    rel_tasks = rel_to_tasks[rel_type]
    if (primary := rel_tasks.get("eq_update")) is not None:
        setattr(
            TestEqualFieldsCheck,
            f"test_equal_fields_update_a_number_error_{rel_type}".replace(":", "_"),
            TestEqualFieldsCheck.get_base_test_update_equal_field_error_fn(
                rel_type, "a_number"
            ),
        )
        if primary:
            setattr(
                TestEqualFieldsCheck,
                f"test_equal_fields_update_a_number_error_back_{rel_type}".replace(
                    ":", "_"
                ),
                TestEqualFieldsCheck.get_base_test_update_equal_field_error_fn(
                    rel_type, "a_number", back=True
                ),
            )
            setattr(
                TestEqualFieldsCheck,
                f"test_equal_fields_update_a_number_success_{rel_type}".replace(
                    ":", "_"
                ),
                TestEqualFieldsCheck.get_base_test_update_equal_field_success_fn(
                    rel_type, "a_number"
                ),
            )
    if (primary := rel_tasks.get("back")) is not None:
        setattr(
            TestEqualFieldsCheck,
            f"test_equal_fields_{equal_field}_create_error_back_{rel_type}".replace(
                ":", "_"
            ),
            TestEqualFieldsCheck.get_base_test_create_fail_fn(
                rel_type, equal_field, back=True
            ),
        )
        if primary:
            setattr(
                TestEqualFieldsCheck,
                f"test_equal_fields_{equal_field}_create_success_back_{rel_type}".replace(
                    ":", "_"
                ),
                TestEqualFieldsCheck.get_base_test_create_success_fn(
                    rel_type, equal_field, back=True
                ),
            )
            setattr(
                TestEqualFieldsCheck,
                f"test_equal_fields_{equal_field}_delete_success_back_{rel_type}".replace(
                    ":", "_"
                ),
                TestEqualFieldsCheck.get_base_test_delete_fn(
                    rel_type, equal_field, back=True
                ),
            )
    if (primary := rel_tasks.get("to")) is not None:
        setattr(
            TestEqualFieldsCheck,
            f"test_equal_fields_{equal_field}_create_error_{rel_type}".replace(
                ":", "_"
            ),
            TestEqualFieldsCheck.get_base_test_create_fail_fn(rel_type, equal_field),
        )
        if primary:
            setattr(
                TestEqualFieldsCheck,
                f"test_equal_fields_{equal_field}_create_success_{rel_type}".replace(
                    ":", "_"
                ),
                TestEqualFieldsCheck.get_base_test_create_success_fn(
                    rel_type, equal_field
                ),
            )
            setattr(
                TestEqualFieldsCheck,
                f"test_equal_fields_{equal_field}_delete_success_{rel_type}".replace(
                    ":", "_"
                ),
                TestEqualFieldsCheck.get_base_test_delete_fn(rel_type, equal_field),
            )
    if (primary := rel_tasks.get("update")) is not None:
        setattr(
            TestEqualFieldsCheck,
            f"test_equal_fields_{equal_field}_update_error_{rel_type}".replace(
                ":", "_"
            ),
            TestEqualFieldsCheck.get_base_test_update_fail_fn(rel_type, equal_field),
        )
        if primary:
            setattr(
                TestEqualFieldsCheck,
                f"test_equal_fields_{equal_field}_update_error_back_{rel_type}".replace(
                    ":", "_"
                ),
                TestEqualFieldsCheck.get_base_test_update_fail_fn(
                    rel_type, equal_field, back=True
                ),
            )
            setattr(
                TestEqualFieldsCheck,
                f"test_equal_fields_{equal_field}_update_success_{rel_type}".replace(
                    ":", "_"
                ),
                TestEqualFieldsCheck.get_base_test_update_success_fn(
                    rel_type, equal_field
                ),
            )
            setattr(
                TestEqualFieldsCheck,
                f"test_equal_fields_{equal_field}_update_success_back_{rel_type}".replace(
                    ":", "_"
                ),
                TestEqualFieldsCheck.get_base_test_update_success_fn(
                    rel_type, equal_field, back=True
                ),
            )
