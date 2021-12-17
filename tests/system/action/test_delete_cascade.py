from openslides_backend.action.generics.delete import DeleteAction
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection

from .base import BaseActionTestCase


class FakeModelCDA(Model):
    collection = Collection("fake_model_cd_a")
    verbose_name = "fake model for cascade deletion a"
    id = fields.IntegerField()

    fake_model_cd_b = fields.RelationField(
        to={Collection("fake_model_cd_b"): "fake_model_cd_a"},
        on_delete=fields.OnDelete.CASCADE,
    )
    fake_model_cd_c = fields.RelationField(
        to={Collection("fake_model_cd_c"): "fake_model_cd_a"},
        on_delete=fields.OnDelete.CASCADE,
    )
    fake_model_cd_b_set_null = fields.RelationField(
        to={Collection("fake_model_cd_b"): "fake_model_cd_a_set_null"},
        on_delete=fields.OnDelete.SET_NULL,
    )
    fake_model_cd_b_set_null_required = fields.RelationField(
        to={Collection("fake_model_cd_b"): "fake_model_cd_a_set_null_required"},
        on_delete=fields.OnDelete.SET_NULL,
    )


class FakeModelCDB(Model):
    collection = Collection("fake_model_cd_b")
    verbose_name = "fake model for cascade deletion b"
    id = fields.IntegerField()

    fake_model_cd_a = fields.RelationField(
        to={Collection("fake_model_cd_a"): "fake_model_cd_b"}
    )
    fake_model_cd_c_protect = fields.RelationField(
        to={Collection("fake_model_cd_c"): "fake_model_cd_b_protected"},
        on_delete=fields.OnDelete.PROTECT,
    )
    fake_model_cd_c_cascade = fields.RelationField(
        to={Collection("fake_model_cd_c"): "fake_model_cd_b_cascaded"},
        on_delete=fields.OnDelete.CASCADE,
    )
    fake_model_cd_a_set_null = fields.RelationField(
        to={Collection("fake_model_cd_a"): "fake_model_cd_b_set_null"},
    )
    fake_model_cd_a_set_null_required = fields.RelationField(
        to={Collection("fake_model_cd_a"): "fake_model_cd_b_set_null_required"},
        required=True,
    )


class FakeModelCDC(Model):
    collection = Collection("fake_model_cd_c")
    verbose_name = "fake model for cascade deletion c"
    id = fields.IntegerField()

    fake_model_cd_a = fields.RelationField(
        to={Collection("fake_model_cd_a"): "fake_model_cd_c"}
    )
    fake_model_cd_b_protected = fields.RelationField(
        to={Collection("fake_model_cd_b"): "fake_model_cd_c_protect"}
    )
    fake_model_cd_b_cascaded = fields.RelationField(
        to={Collection("fake_model_cd_b"): "fake_model_cd_c_cascade"}
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


class TestDeleteCascade(BaseActionTestCase):
    def test_simple(self) -> None:
        self.set_models(
            {
                "fake_model_cd_a/1": {"fake_model_cd_b": 1},
                "fake_model_cd_b/1": {"fake_model_cd_a": 1},
            }
        )
        response = self.request("fake_model_cd_a.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("fake_model_cd_a/1")
        self.assert_model_deleted("fake_model_cd_b/1")

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
        self.assert_model_deleted("fake_model_cd_a/1")
        self.assert_model_deleted("fake_model_cd_b/1")
        self.assert_model_deleted("fake_model_cd_c/1")

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
            "You can not delete fake_model_cd_b/1 because you have to delete the following related models first: [FullQualifiedId('fake_model_cd_c/1')]",
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
        self.assert_model_deleted("fake_model_cd_b/1")

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
            "You can not delete fake_model_cd_a/1 because you have to delete the following related models first: [FullQualifiedId('fake_model_cd_c/1')]",
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
        self.assert_model_deleted("fake_model_cd_a/1")
        self.assert_model_deleted("fake_model_cd_b/1")
        self.assert_model_deleted("fake_model_cd_c/1")

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
        self.assert_model_deleted("fake_model_cd_a/1")
        self.assert_model_exists(
            "fake_model_cd_b/1", {"fake_model_cd_a_set_null": None}
        )

    def test_set_null_required(self) -> None:
        self.set_models(
            {
                "fake_model_cd_a/1": {
                    "fake_model_cd_b_set_null_required": 1,
                },
                "fake_model_cd_b/1": {"fake_model_cd_a_set_null_required": 1},
            }
        )
        response = self.request("fake_model_cd_a.delete", {"id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Update of fake_model_cd_b/1: You try to set following required fields to an empty value: ['fake_model_cd_a_set_null_required']",
            response.json["message"],
        )
        self.assert_model_exists(
            "fake_model_cd_a/1", {"fake_model_cd_b_set_null_required": 1}
        )
        self.assert_model_exists(
            "fake_model_cd_b/1", {"fake_model_cd_a_set_null_required": 1}
        )
