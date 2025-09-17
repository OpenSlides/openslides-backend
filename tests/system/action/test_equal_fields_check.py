from pytest import mark

from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model

from .base_generic import BaseGenericTestCase


class FakeModelEFA(Model):
    collection = "fake_model_ef_a"
    verbose_name = "fake model for equal field check a"
    id = fields.IntegerField()

    b_id = fields.RelationField(
        to={"fake_model_ef_b": "meeting_id"}, is_view_field=True
    )
    c_ids = fields.RelationListField(
        to={"fake_model_ef_c": "meeting_id"}, is_view_field=True
    )


class FakeModelEFB(Model):
    collection = "fake_model_ef_b"
    verbose_name = "fake model for equal field check b"
    id = fields.IntegerField()

    meeting_id = fields.RelationField(to={"fake_model_ef_a": "b_id"})

    c_id = fields.RelationField(
        to={"fake_model_ef_c": "b_id"},
        equal_fields="meeting_id",
    )
    c_ids = fields.RelationListField(
        to={"fake_model_ef_c": "b_ids"}, equal_fields="meeting_id", is_view_field=True
    )
    c_generic_id = fields.GenericRelationField(
        to={"fake_model_ef_c": "b_generic_id"},
        equal_fields="meeting_id",
    )
    c_generic_ids = fields.GenericRelationListField(
        to={"fake_model_ef_c": "b_generic_ids"},
        equal_fields="meeting_id",
        is_view_field=True,
    )


class FakeModelEFC(Model):
    collection = "fake_model_ef_c"
    verbose_name = "fake model for equal field check c"
    id = fields.IntegerField()

    meeting_id = fields.RelationField(to={"fake_model_ef_a": "c_ids"})

    b_id = fields.RelationField(to={"fake_model_ef_b": "c_id"}, is_view_field=True)
    b_ids = fields.RelationListField(
        to={"fake_model_ef_b": "c_ids"}, is_view_field=True
    )
    b_generic_id = fields.GenericRelationField(
        to={"fake_model_ef_b": "c_generic_id"}, is_view_field=True
    )
    b_generic_ids = fields.GenericRelationListField(
        to={"fake_model_ef_b": "c_generic_ids"}, is_view_field=True
    )


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


class TestEqualFieldsCheck(BaseGenericTestCase):
    collection_a = "fake_model_ef_a"
    collection_b = "fake_model_ef_b"
    collection_c = "fake_model_ef_c"
    tables_to_reset = [
        f"{collection_a}_t",
        f"{collection_b}_t",
        f"{collection_c}_t",
        "nm_fake_model_ef_b_c_ids_fake_model_ef_c_t",
    ]
    yml = f"""
    _meta:
        id_field: &id_field
            type: number
            restriction_mode: A
            constant: true
            required: true
    {collection_a}:
        id: *id_field
        b_id:
            type: relation
            to: {collection_b}/meeting_id
            reference: {collection_b}
        c_ids:
            type: relation-list
            to: {collection_c}/meeting_id
            reference: {collection_c}
    {collection_b}:
        id: *id_field
        meeting_id:
            type: relation
            to: {collection_a}/b_id
            reference: {collection_a}
        c_id:
            type: relation
            to: {collection_c}/b_id
            reference: {collection_c}
            equal_fields: meeting_id
        c_ids:
            type: relation-list
            to: {collection_c}/b_ids
            equal_fields: meeting_id
        c_generic_id:
            type: generic-relation
            reference:
            - {collection_c}
            to:
            - {collection_c}/b_generic_id
            equal_fields: meeting_id
        c_generic_ids:
            type: generic-relation-list
            to:
            collections:
                - {collection_c}
            field: b_generic_ids
            equal_fields: meeting_id
    {collection_c}:
        id: *id_field
        meeting_id:
            type: relation
            to: {collection_a}/c_ids
            reference: {collection_a}
        b_id:
            type: relation
            to: {collection_b}/c_id
            reference: {collection_b}
            equal_fields: meeting_id
        b_ids:
            type: relation-list
            to: {collection_b}/c_ids
            equal_fields: meeting_id
        b_generic_id:
            type: generic-relation
            reference:
            - {collection_b}
            to:
            - {collection_b}/c_generic_id
            equal_fields: meeting_id
        b_generic_ids:
            type: generic-relation-list
            to:
            collections:
                - {collection_b}
            field: c_generic_ids
            equal_fields: meeting_id
    """

    def test_simple_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"c_ids": [1]},
                "fake_model_ef_c/1": {"meeting_id": 1},
            }
        )
        response = self.request("fake_model_ef_b.create", {"meeting_id": 1, "c_id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1")

    def test_simple_fail(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {},
                "fake_model_ef_a/2": {"c_ids": [1]},
                "fake_model_ef_c/1": {"meeting_id": 2},
            }
        )
        response = self.request("fake_model_ef_b.create", {"meeting_id": 1, "c_id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['fake_model_ef_c/1']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_ef_b/1")

    def test_simple_update_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"b_id": 1, "c_ids": [1, 2]},
                "fake_model_ef_b/1": {"meeting_id": 1, "c_id": 1},
                "fake_model_ef_c/1": {"meeting_id": 1, "b_id": 1},
                "fake_model_ef_c/2": {"meeting_id": 1},
            }
        )
        response = self.request("fake_model_ef_b.update", {"id": 1, "c_id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1", {"c_id": 2})

    def test_list_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"c_ids": [1]},
                "fake_model_ef_c/1": {"meeting_id": 1},
            }
        )
        response = self.request(
            "fake_model_ef_b.create", {"meeting_id": 1, "c_ids": [1]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1")

    def test_list_fail(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {},
                "fake_model_ef_a/2": {"c_ids": [1]},
                "fake_model_ef_c/1": {"meeting_id": 2},
            }
        )
        response = self.request(
            "fake_model_ef_b.create", {"meeting_id": 1, "c_ids": [1]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['fake_model_ef_c/1']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_ef_b/1")

    def test_generic_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"c_ids": [1]},
                "fake_model_ef_c/1": {"meeting_id": 1},
            }
        )
        response = self.request(
            "fake_model_ef_b.create",
            {"meeting_id": 1, "c_generic_id": "fake_model_ef_c/1"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1")

    def test_generic_fail(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {},
                "fake_model_ef_a/2": {"c_ids": [1]},
                "fake_model_ef_c/1": {"meeting_id": 2},
            }
        )
        response = self.request(
            "fake_model_ef_b.create",
            {"meeting_id": 1, "c_generic_id": "fake_model_ef_c/1"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['fake_model_ef_c/1']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_ef_b/1")

    @mark.skip(
        "Currently generic relation lists on both ends aren't used. DDL should be fixed then."
    )
    def test_generic_list_pass(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {"c_ids": [1]},
                "fake_model_ef_c/1": {"meeting_id": 1},
            }
        )
        response = self.request(
            "fake_model_ef_b.create",
            {"meeting_id": 1, "c_generic_ids": ["fake_model_ef_c/1"]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ef_b/1")

    def test_generic_list_fail(self) -> None:
        self.set_models(
            {
                "fake_model_ef_a/1": {},
                "fake_model_ef_a/2": {"c_ids": [1]},
                "fake_model_ef_c/1": {"meeting_id": 2},
            }
        )
        response = self.request(
            "fake_model_ef_b.create",
            {"meeting_id": 1, "c_generic_ids": ["fake_model_ef_c/1"]},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 1: ['fake_model_ef_c/1']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_ef_b/1")
