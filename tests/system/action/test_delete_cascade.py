from openslides_backend.action.generics.delete import DeleteAction
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model

from .base_generic import BaseGenericTestCase


class FakeModelCDA(Model):
    collection = "fake_model_cd_a"
    verbose_name = "fake model for cascade deletion a"
    id = fields.IntegerField()

    fake_model_cd_b = fields.RelationField(
        to={"fake_model_cd_b": "fake_model_cd_a"},
        on_delete=fields.OnDelete.CASCADE,
        is_view_field=True,
    )
    fake_model_cd_c = fields.RelationField(
        to={"fake_model_cd_c": "fake_model_cd_a"},
        on_delete=fields.OnDelete.CASCADE,
        is_view_field=True,
    )
    fake_model_cd_b_set_null = fields.RelationField(
        to={"fake_model_cd_b": "fake_model_cd_a_set_null"},
        on_delete=fields.OnDelete.SET_NULL,
        is_view_field=True,
    )
    fake_model_cd_d_set_null_required = fields.RelationField(
        to={"fake_model_cd_d": "fake_model_cd_a_set_null_required"},
        on_delete=fields.OnDelete.SET_NULL,
        is_view_field=True,
    )


class FakeModelCDB(Model):
    collection = "fake_model_cd_b"
    verbose_name = "fake model for cascade deletion b"
    id = fields.IntegerField()

    fake_model_cd_a = fields.RelationField(to={"fake_model_cd_a": "fake_model_cd_b"})
    fake_model_cd_c_protect = fields.RelationField(
        to={"fake_model_cd_c": "fake_model_cd_b_protected"},
        on_delete=fields.OnDelete.PROTECT,
        is_view_field=True,
    )
    fake_model_cd_c_cascade = fields.RelationField(
        to={"fake_model_cd_c": "fake_model_cd_b_cascaded"},
        on_delete=fields.OnDelete.CASCADE,
        is_view_field=True,
    )
    fake_model_cd_a_set_null = fields.RelationField(
        to={"fake_model_cd_a": "fake_model_cd_b_set_null"},
    )


class FakeModelCDC(Model):
    collection = "fake_model_cd_c"
    verbose_name = "fake model for cascade deletion c"
    id = fields.IntegerField()

    fake_model_cd_a = fields.RelationField(to={"fake_model_cd_a": "fake_model_cd_c"})
    fake_model_cd_b_protected = fields.RelationField(
        to={"fake_model_cd_b": "fake_model_cd_c_protect"}
    )
    fake_model_cd_b_cascaded = fields.RelationField(
        to={"fake_model_cd_b": "fake_model_cd_c_cascade"}
    )


class FakeModelCDD(Model):
    collection = "fake_model_cd_d"
    verbose_name = "fake model for cascade deletion d"
    id = fields.IntegerField()

    fake_model_cd_a_set_null_required = fields.RelationField(
        to={"fake_model_cd_a": "fake_model_cd_d_set_null_required"},
        required=True,
    )


@register_action("fake_model_cd_a.delete", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelCDADeleteAction(DeleteAction):
    model = FakeModelCDA()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_cd_b.delete", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelCDBDeleteAction(DeleteAction):
    model = FakeModelCDB()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_cd_c.delete", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelCDCDeleteAction(DeleteAction):
    model = FakeModelCDC()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_cd_d.delete", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelCDDDeleteAction(DeleteAction):
    model = FakeModelCDC()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


class TestDeleteCascade(BaseGenericTestCase):
    collection_a = "fake_model_cd_a"
    collection_b = "fake_model_cd_b"
    collection_c = "fake_model_cd_c"
    collection_d = "fake_model_cd_d"
    tables_to_reset = [
        f"{collection_a}_t",
        f"{collection_b}_t",
        f"{collection_c}_t",
        f"{collection_d}_t",
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
        {collection_b}:
            type: relation
            to: {collection_b}/{collection_a}
            on_delete: CASCADE
        {collection_c}:
            type: relation
            to: {collection_c}/{collection_a}
            on_delete: CASCADE
        {collection_b}_set_null:
            type: relation
            to: {collection_b}/{collection_a}_set_null
            on_delete: SET_NULL
        {collection_d}_set_null_required:
            type: relation
            to: {collection_d}/{collection_a}_set_null_required
            on_delete: SET_NULL
    {collection_b}:
        id: *id_field
        {collection_a}:
            type: relation
            to: {collection_a}/{collection_b}
            reference: {collection_a}
        {collection_c}_protect:
            type: relation
            to: {collection_c}/{collection_b}_protected
            on_delete: PROTECT
        {collection_c}_cascade:
            type: relation
            to: {collection_c}/{collection_b}_cascaded
            on_delete: CASCADE
        {collection_a}_set_null:
            type: relation
            to: {collection_a}/{collection_b}_set_null
            reference: {collection_a}
    {collection_c}:
        id: *id_field
        {collection_a}:
            type: relation
            to: {collection_a}/{collection_c}
            reference: {collection_a}
        {collection_b}_protected:
            type: relation
            to: {collection_b}/{collection_c}_protect
            reference: {collection_b}
        {collection_b}_cascaded:
            type: relation
            to: {collection_b}/{collection_c}_cascade
            reference: {collection_b}
    {collection_d}:
        id: *id_field
        {collection_a}_set_null_required:
            type: relation
            to: {collection_a}/{collection_d}_set_null_required
            reference: {collection_a}
            required: true
    """

    def test_simple(self) -> None:
        self.set_models(
            {
                "fake_model_cd_a/1": {"fake_model_cd_b": 1},
                "fake_model_cd_b/1": {"fake_model_cd_a": 1},
            }
        )
        response = self.request("fake_model_cd_a.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("fake_model_cd_a/1")
        self.assert_model_not_exists("fake_model_cd_b/1")

    def test_double_cascade(self) -> None:
        self.set_models(
            {
                "fake_model_cd_a/1": {"fake_model_cd_b": 1},
                "fake_model_cd_b/1": {
                    "fake_model_cd_a": 1,
                    "fake_model_cd_c_cascade": 1,
                },
                "fake_model_cd_c/1": {"fake_model_cd_b_cascaded": 1},
            }
        )
        response = self.request("fake_model_cd_a.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("fake_model_cd_a/1")
        self.assert_model_not_exists("fake_model_cd_b/1")
        self.assert_model_not_exists("fake_model_cd_c/1")

    def test_simple_protect(self) -> None:
        self.set_models(
            {
                "fake_model_cd_b/1": {
                    "fake_model_cd_c_protect": 1,
                },
                "fake_model_cd_c/1": {"fake_model_cd_b_protected": 1},
            }
        )
        response = self.request("fake_model_cd_b.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "You can not delete fake_model_cd_b/1 because you have to delete the following related models first: ['fake_model_cd_c/1']",
            response.json["message"],
        )
        self.assert_model_exists("fake_model_cd_b/1")
        self.assert_model_exists("fake_model_cd_c/1")

    def test_protect_not_filled(self) -> None:
        self.set_models(
            {
                "fake_model_cd_b/1": {
                    "fake_model_cd_c_protect": None,
                },
            }
        )
        response = self.request("fake_model_cd_b.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("fake_model_cd_b/1")

    def test_cascade_protect(self) -> None:
        self.set_models(
            {
                "fake_model_cd_a/1": {"fake_model_cd_b": 1},
                "fake_model_cd_b/1": {
                    "fake_model_cd_a": 1,
                    "fake_model_cd_c_protect": 1,
                },
                "fake_model_cd_c/1": {"fake_model_cd_b_protected": 1},
            }
        )
        response = self.request("fake_model_cd_a.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "You can not delete fake_model_cd_a/1 because you have to delete the following related models first: ['fake_model_cd_c/1']",
            response.json["message"],
        )
        self.assert_model_exists("fake_model_cd_a/1")
        self.assert_model_exists("fake_model_cd_b/1")
        self.assert_model_exists("fake_model_cd_c/1")

    def test_cascade_overwrite_protect(self) -> None:
        self.set_models(
            {
                "fake_model_cd_a/1": {"fake_model_cd_b": 1, "fake_model_cd_c": 1},
                "fake_model_cd_b/1": {
                    "fake_model_cd_a": 1,
                    "fake_model_cd_c_protect": 1,
                },
                "fake_model_cd_c/1": {
                    "fake_model_cd_a": 1,
                    "fake_model_cd_b_protected": 1,
                },
            }
        )
        response = self.request("fake_model_cd_a.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("fake_model_cd_a/1")
        self.assert_model_not_exists("fake_model_cd_b/1")
        self.assert_model_not_exists("fake_model_cd_c/1")

    def test_set_null(self) -> None:
        self.set_models(
            {
                "fake_model_cd_a/1": {
                    "fake_model_cd_b_set_null": 1,
                },
                "fake_model_cd_b/1": {"fake_model_cd_a_set_null": 1},
            }
        )
        response = self.request("fake_model_cd_a.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("fake_model_cd_a/1")
        self.assert_model_exists(
            "fake_model_cd_b/1", {"fake_model_cd_a_set_null": None}
        )

    def test_set_null_required(self) -> None:
        self.set_models(
            {
                "fake_model_cd_a/1": {},
                "fake_model_cd_d/1": {"fake_model_cd_a_set_null_required": 1},
            }
        )
        response = self.request("fake_model_cd_a.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Update of fake_model_cd_d/1: You try to set following required fields to an empty value: ['fake_model_cd_a_set_null_required']",
            response.json["message"],
        )
        self.assert_model_exists(
            "fake_model_cd_a/1", {"fake_model_cd_d_set_null_required": 1}
        )
        self.assert_model_exists(
            "fake_model_cd_d/1", {"fake_model_cd_a_set_null_required": 1}
        )
