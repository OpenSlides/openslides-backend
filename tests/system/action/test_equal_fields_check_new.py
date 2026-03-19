from copy import deepcopy
from pytest import mark
from typing import Any, Callable
import yaml
from unittest import mock

from cli.generate_models import Attribute, Model
from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.generics.delete import DeleteAction
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from tests.patch_model_registry_helper import FakeModel, PatchModelRegistryMixin
from meta.dev.src import helper_get_names

from .base_generic import BaseGenericTestCase

RefValType = int | str | list[int] | list[str]

collection_a = "fake_model_ef_a"
collection_b = "fake_model_ef_b"
collection_c = "fake_model_ef_c"

# TODO: see if these are really all supported relation types
unturned_check_relations = [
    "1r:1t", #
    "1r:nr", #
    "1r:nt", #
    # "1Gr:1Gr", # Delete not working, field not supported
    "1Gr:nr", #
    "1Gr:nt", #
    "nt:nt",
    "nGt:nt",

    # TODO: Testing with required fields still _requires_ some adjustment of the tests.
    # "1rR:1t"
    # "1rR:nr",
    # "1r:ntR",
    # "1rR:nt",
    # "1GrR:nt",
    # "nt:ntR",
    # "1Gr:1tR",
    # "1GrR:1tR",
    # "1GrR:1t",
]
def turn_relation(relation:str) -> str:
    type1,type2 = relation.split(":")
    return f"{type2}:{type1}"
check_relations = [*unturned_check_relations, *[
    turned_relation for relation in unturned_check_relations if (turned_relation:=turn_relation(relation)) != relation
]]


def interpret_field_type(field_type: str)-> tuple[bool, bool, bool]:
    """
    Returns multiple, generic, reference
    """
    return "n" in field_type, "G" in field_type or "g" in field_type, "r" in field_type

def generate_collection_field_name(prefix:str, field_type: str, rel_name:str, back: bool=False) -> tuple[str, bool]:
    prefix = "" if prefix == "meeting_id" else prefix
    name = prefix + "_" if prefix else ""
    name += rel_name.replace("1", "one").replace("R","q").replace(":","_").lower()
    if back:
        name += "_back"
    if "1" in field_type or "one" in field_type:
        return name + "_id", False
    else:
        return name + "_ids", True



def generate_collection_field_def(name:str, field_type:str, multi:bool, back_coll:str, back_name: str, equal_field:str|None=None) -> str:
    buffer = "                "
    definition = f"{name}:\n{buffer}type: "
    if generic:=("G" in field_type or "G" in field_type):
        definition += "generic-"
    definition += "relation"
    if multi:
        definition += f"-list"
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


def generate_collection_field_defs(coll_name: str, back_coll_name: str, rel_type: str, equal_field: str) -> tuple[str, str]:
    first, second = rel_type.split(":")
    first_name, first_multi = generate_collection_field_name(equal_field,first,rel_type)
    second_name, second_multi = generate_collection_field_name(equal_field,second,rel_type, True)
    first_def = generate_collection_field_def(first_name, first, first_multi, back_coll_name, second_name, equal_field)
    second_def = generate_collection_field_def(second_name, second, second_multi, coll_name, first_name)
    return first_def, second_def

def generate_collection_fields(coll_name1:str, coll_name2:str, rel_types:list[str], equal_fields: list[str])->tuple[str,str]:
    definition1=""
    definition2=""
    buffer = "            "
    for rel_type in rel_types:
        types = [rel_type]
        for a_type in types:
            for equal_field in equal_fields:
                no1, no2 = generate_collection_field_defs(coll_name1, coll_name2, a_type, equal_field)
                definition1 += f"\n{buffer}{no1}"
                definition2 += f"\n{buffer}{no2}"
    return definition1, definition2

definition1, definition2 = generate_collection_fields(collection_b, collection_c, check_relations, ["a_number","meeting_id"])
final_yml = f"""
    _meta:
        id_field: &id_field
            type: number
            restriction_mode: A
            constant: true
            required: true
    {collection_a}:
        fields:
            id: *id_field
            b_id:
                type: relation
                to: {collection_b}/meeting_id
            c_ids:
                type: relation-list
                to: {collection_c}/meeting_id
                reference: {collection_c}
    {collection_b}:
        fields:
            id: *id_field
            a_number:
                type: number
            meeting_id:
                type: relation
                to: {collection_a}/b_id
                reference: {collection_a}{definition1}
    {collection_c}:
        fields:
            id: *id_field
            a_number:
                type: number
            meeting_id:
                type: relation
                to: {collection_a}/c_ids
                reference: {collection_a}{definition2}
    """

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

class FakeModelEFB(FakeModel):
    collection = "fake_model_ef_b"
    verbose_name = "fake model for equal field check b"
    id = fields.IntegerField()

    meeting_id = fields.RelationField(to={"fake_model_ef_a": "b_id"})
    a_number = fields.IntegerField()
    

class FakeModelEFC(FakeModel):
    collection = "fake_model_ef_c"
    verbose_name = "fake model for equal field check c"
    id = fields.IntegerField()

    meeting_id = fields.RelationField(to={"fake_model_ef_a": "c_ids"})
    a_number = fields.IntegerField()

@register_action("fake_model_ef_b.create", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelEFBCreateAction(CreateAction):
    model = FakeModelEFB()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_ef_b.update", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelEFBUpdateAction(UpdateAction):
    model = FakeModelEFB()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True

@register_action("fake_model_ef_b.delete", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelEFBDeleteAction(DeleteAction):
    model = FakeModelEFB()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True

@register_action("fake_model_ef_c.create", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelEFCCreateAction(CreateAction):
    model = FakeModelEFC()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_ef_c.update", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelEFCUpdateAction(UpdateAction):
    model = FakeModelEFC()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True

@register_action("fake_model_ef_c.delete", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelEFCDeleteAction(DeleteAction):
    model = FakeModelEFC()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


def get_attr_helper(collection: str, field_name:str, attr_data: Attribute) -> Any:
    to_data=attr_data.to
    to = to_data.to if to_data else {}
    match attr_data.type:
        case "generic-relation-list":
            field = fields.GenericRelationListField(
                to=to,
                is_view_field=attr_data.is_view_field,
                write_fields=attr_data.write_fields,
                is_primary=attr_data.is_primary,
                required=attr_data.required
            )
        case "relation-list":
            field = fields.RelationListField(
                to=to,
                is_view_field=attr_data.is_view_field,
                write_fields=attr_data.write_fields,
                is_primary=attr_data.is_primary,
                required=attr_data.required
            )
        case "generic-relation":
            field = fields.GenericRelationField(
                to=to,
                is_view_field=attr_data.is_view_field,
                write_fields=attr_data.write_fields,
                is_primary=attr_data.is_primary,
                required=attr_data.required
            )
        case "relation":
            field = fields.RelationField(
                to=to,
                is_view_field=attr_data.is_view_field,
                write_fields=attr_data.write_fields,
                is_primary=attr_data.is_primary,
                required=attr_data.required
            )
        case _:
            raise Exception("get_attr_helper shouldn't be called for non-relations.")
    field.own_field_name = field_name
    field.own_collection = collection
    return field


# 1r(meeting_id):1r
# 1r(meeting_id):nr
class TestEqualFieldsCheck(PatchModelRegistryMixin, BaseGenericTestCase):
    yml = final_yml
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        orig_build_models_yaml_content = helper_get_names.build_models_yaml_content
        helper_get_names.build_models_yaml_content = mock.Mock()
        helper_get_names.build_models_yaml_content.return_value = final_yml.encode()
        loaded_yml: dict[str,dict[str,Any]] = yaml.safe_load(final_yml)
        efb_model = Model(collection_b, loaded_yml[collection_b]["fields"])
        efc_model = Model(collection_c, loaded_yml[collection_c]["fields"])
        for rel_type in check_relations:
            for equal_field in ["meeting_id", "a_number"]:
                b_name = generate_collection_field_name(equal_field, rel_type.split(":")[0], rel_type)[0]
                efb_attr = efb_model.attributes[b_name]
                c_name =generate_collection_field_name(equal_field, rel_type.split(":")[1], rel_type, True)[0]
                efc_attr = efc_model.attributes[c_name]
                setattr(FakeModelEFB, b_name, get_attr_helper(collection_b, b_name,efb_attr))
                setattr(FakeModelEFC, c_name, get_attr_helper(collection_c,c_name,efc_attr))
        helper_get_names.build_models_yaml_content = orig_build_models_yaml_content


    def setUp(self) -> None:
        super().setUp()
        self.set_models({
            f"{collection_a}/1": {},
            f"{collection_a}/4": {},
        })
    
    def get_reference_value(self, val: int, multiple:bool, generic:bool, target_coll:str) -> RefValType:
        if generic:
            return_val = f"{target_coll}/{val}"
            if multiple:
                return [return_val]
        else:
            return_val = val
            if multiple:
                return [return_val]
        return return_val
    
    def get_test_relation_data(self, rel_type: str, equal_field: str) -> tuple[str,RefValType,str,RefValType]:
        field1_type, field2_type = rel_type.split(":")
        multiple1, generic1, reference1 = interpret_field_type(field1_type)
        multiple2, generic2, reference2 = interpret_field_type(field2_type)
        field1, _ = generate_collection_field_name(equal_field, field1_type, rel_type)
        field2, _ = generate_collection_field_name(equal_field, field2_type, rel_type, True)
        ref_val1 =self.get_reference_value(1,multiple1, generic1, collection_c)
        ref_val2 =self.get_reference_value(1,multiple2, generic2, collection_b)
        return field1,ref_val1,field2, ref_val2

    @classmethod
    def get_base_test_create_success_fn(cls, rel_type: str, equal_field: str= "meeting_id", back:bool=False)->Callable:
        def base_test_success(self) -> None:
            field1,ref_val1,field2, ref_val2 = self.get_test_relation_data(rel_type, equal_field)
            self.set_models({f"{collection_b if back else collection_c}/1": {equal_field:1}})
            response = self.request(f"{collection_c if back else collection_b}.create", {equal_field: 1, field2 if back else field1: ref_val2 if back else ref_val1})
            self.assert_status_code(response, 200)
            data ={
                f"{collection_b}/1": {equal_field:1,field1: ref_val1},
                f"{collection_c}/1": {equal_field:1,field2: ref_val2},
            }
            for fqid, date in data.items():
                self.assert_model_exists(fqid, date)
        return base_test_success

    @classmethod
    def get_base_test_update_success_fn(cls, rel_type: str, equal_field: str= "meeting_id", back:bool=False)->Callable:
        def base_test_success(self) -> None:
            field1,ref_val1,field2, ref_val2 = self.get_test_relation_data(rel_type, equal_field)
            self.set_models({
                f"{collection_b}/1": {equal_field:1},
                f"{collection_c}/1": {equal_field:1}
            })
            response = self.request(f"{collection_c if back else collection_b}.update", {"id":1,equal_field: 1, field2 if back else field1: ref_val2 if back else ref_val1})
            self.assert_status_code(response, 200)
            data ={
                f"{collection_b}/1": {equal_field:1,field1: ref_val1},
                f"{collection_c}/1": {equal_field:1,field2: ref_val2},
            }
            for fqid, date in data.items():
                self.assert_model_exists(fqid, date)
        return base_test_success


    def assert_fail_test_error(self, response: Any, equal_field: str, back: bool, field1:str,field2:str) -> None:
        self.assert_status_code(response, 400)
        shortened = response.json["message"].split("\nCONTEXT:")[0]
        if equal_field == "meeting_id":
            if "to meeting 4:" in shortened:
                self.assertEqual(f"Relation violates required constraint: The following models do not belong to meeting 4: ['{collection_b if back else collection_c}/1']", shortened)
            else:
                self.assertEqual(f"Relation violates required constraint: The following models do not belong to meeting 1: ['{collection_c if back else collection_b}/1']", shortened)
        else:
            expect_field = field1 if field1 in shortened else field2
            for coll in [collection_b, collection_c]:
                if (generic_relation_name:=f"{expect_field}_{coll}_id") in shortened:
                    expect_field=generic_relation_name
            self.assertIn(f"Relation violates required constraint: The relation {expect_field} requires the following fields to be equal:", shortened)
            self.assertIn(f"\n {collection_b if back else collection_c}/1/a_number: 1", shortened)
            self.assertIn(f"\n {collection_c if back else collection_b}/1/a_number: 4", shortened)

    @classmethod
    def get_base_test_create_fail_fn(cls, rel_type: str, equal_field: str= "meeting_id", back:bool=False)->Callable:
        def base_test_fail(self) -> None:
            field1,ref_val1,field2, ref_val2 = self.get_test_relation_data(rel_type, equal_field)
            self.set_models({f"{collection_b if back else collection_c}/1": {equal_field:1}})
            response = self.request(f"{collection_c if back else collection_b}.create", {equal_field: 4, field2 if back else field1: ref_val2 if back else ref_val1})
            self.assert_fail_test_error(response,equal_field,back, field1, field2)
        return base_test_fail

    @classmethod
    def get_base_test_update_fail_fn(cls, rel_type: str, equal_field: str= "meeting_id", back:bool=False)->Callable:
        def base_test_fail(self) -> None:
            field1,ref_val1,field2, ref_val2 = self.get_test_relation_data(rel_type, equal_field)
            self.set_models({
                f"{collection_b if back else collection_c}/1": {equal_field:1},
                f"{collection_c if back else collection_b}/1": {equal_field:4}
            })
            response = self.request(f"{collection_c if back else collection_b}.update", {"id":1,equal_field: 4, field2 if back else field1: ref_val2 if back else ref_val1})
            self.assert_fail_test_error(response,equal_field,back, field1, field2)
        return base_test_fail
    
    @classmethod
    def get_base_test_delete_fn(cls, rel_type: str, equal_field: str= "meeting_id", back:bool=False) -> Callable:
        def base_test_delete(self) -> None:
            field1,ref_val1,field2, ref_val2 = self.get_test_relation_data(rel_type, equal_field)
            self.set_models({
                f"{collection_b}/1": {equal_field:1, field1:ref_val1},
                f"{collection_c}/1": {equal_field:1, field2:ref_val2}
            })
            response = self.request(f"{collection_c if back else collection_b}.delete", {"id":1})
            self.assert_status_code(response, 200)
        return base_test_delete
    
    @classmethod
    def get_base_test_update_equal_field_success_fn(cls, rel_type: str, equal_field: str= "meeting_id") -> Callable:
        def base_test_update_equal_field(self) -> None:
            field1,ref_val1,field2, ref_val2 = self.get_test_relation_data(rel_type, equal_field)
            self.set_models({
                f"{collection_b}/1": {equal_field:1, field1:ref_val1},
                f"{collection_c}/1": {equal_field:1, field2:ref_val2}
            })
            self.set_models({
                f"{collection_b}/1": {equal_field:4},
                f"{collection_c}/1": {equal_field:4}
            })
            for coll in [collection_b, collection_c]:
                self.assert_model_exists(f"{coll}/1", {equal_field:4})
        return base_test_update_equal_field

    @classmethod
    def get_base_test_update_equal_field_error_fn(cls, rel_type: str, equal_field: str= "meeting_id", back:bool=False) -> Callable:
        def base_test_update_equal_field(self) -> None:
            field1,ref_val1,field2, ref_val2 = self.get_test_relation_data(rel_type, equal_field)
            self.set_models({
                f"{collection_b}/1": {equal_field:1, field1:ref_val1},
                f"{collection_c}/1": {equal_field:1, field2:ref_val2}
            })
            response = self.request(f"{collection_c if back else collection_b}.update", {"id":1, equal_field:4})
            self.assert_fail_test_error(response,equal_field,back, field1, field2)
        return base_test_update_equal_field


for rel_type in check_relations:
    for equal_field in ["meeting_id", "a_number"]:
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_create_error_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_create_fail_fn(rel_type,equal_field))
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_create_error_back_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_create_fail_fn(rel_type,equal_field, back=True))
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_create_success_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_create_success_fn(rel_type,equal_field))
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_create_success_back_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_create_success_fn(rel_type,equal_field, back=True))
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_update_error_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_update_fail_fn(rel_type,equal_field))
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_update_error_back_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_update_fail_fn(rel_type,equal_field, back=True))
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_update_success_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_update_success_fn(rel_type,equal_field))
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_update_success_back_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_update_success_fn(rel_type,equal_field, back=True))
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_delete_success_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_delete_fn(rel_type,equal_field))
        setattr(TestEqualFieldsCheck, f"test_equal_fields_{equal_field}_delete_success_back_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_delete_fn(rel_type,equal_field, back=True))

for rel_type in check_relations:
    setattr(TestEqualFieldsCheck, f"test_equal_fields_update_a_number_error_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_update_equal_field_error_fn(rel_type,"a_number"))
    setattr(TestEqualFieldsCheck, f"test_equal_fields_update_a_number_error_back_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_update_equal_field_error_fn(rel_type,"a_number", back=True))
    setattr(TestEqualFieldsCheck, f"test_equal_fields_update_a_number_success_{rel_type}".replace(":", "_"), TestEqualFieldsCheck.get_base_test_update_equal_field_success_fn(rel_type,"a_number"))
