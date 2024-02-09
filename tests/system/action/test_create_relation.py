from typing import Any

from openslides_backend.action.action import Action
from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.mixins.create_action_with_dependencies import (
    CreateActionWithDependencies,
)
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection

from .base import BaseActionTestCase


class FakeModelCRA(Model):
    collection: Collection = "fake_model_cr_a"
    verbose_name = "fake model for simple field creation"
    id = fields.IntegerField()

    req_field = fields.IntegerField(required=True)
    not_req_field = fields.IntegerField()


class FakeModelCRB(Model):
    collection: Collection = "fake_model_cr_b"
    verbose_name = "fake model for create relation b"
    id = fields.IntegerField()

    name = fields.CharField()
    fake_model_cr_c_id = fields.RelationField(
        to={"fake_model_cr_c": "fake_model_cr_b_id"}, required=True
    )


class FakeModelCRC(Model):
    collection: Collection = "fake_model_cr_c"
    verbose_name = "fake model for create relation c"
    id = fields.IntegerField()

    name = fields.CharField()
    fake_model_cr_b_id = fields.RelationField(
        to={"fake_model_cr_b": "fake_model_cr_c_id"}, required=True
    )
    fake_model_cr_d_id = fields.RelationField(
        to={"fake_model_cr_d": "fake_model_cr_c_ids"},
    )


class FakeModelCRD(Model):
    collection: Collection = "fake_model_cr_d"
    verbose_name = "fake model for create relation d"
    id = fields.IntegerField()

    name = fields.CharField()
    fake_model_cr_c_ids = fields.RelationListField(
        to={"fake_model_cr_c": "fake_model_cr_d_id"}, required=True
    )


@register_action("fake_model_cr_a.create", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelCRACreateAction(CreateAction):
    model = FakeModelCRA()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_cr_c.create", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelCRCCreateAction(CreateAction):
    model = FakeModelCRC()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_cr_b.create", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelCRBCreateAction(CreateActionWithDependencies):
    model = FakeModelCRB()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True

    dependencies = [FakeModelCRCCreateAction]

    def get_dependent_action_data(
        self, instance: dict[str, Any], CreateActionClass: type[Action]
    ) -> list[dict[str, Any]]:
        return [
            {
                "name": "modelC",
                "fake_model_cr_b_id": instance["id"],
            }
        ]


@register_action("fake_model_cr_d.create", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelCRDCreateAction(CreateAction):
    model = FakeModelCRD()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


class TestCreateRelation(BaseActionTestCase):
    def test_simple_create(self) -> None:
        response = self.request(
            "fake_model_cr_a.create", {"req_field": 1, "not_req_field": 2}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "fake_model_cr_a/1", {"req_field": 1, "not_req_field": 2}
        )

    def test_create_without_req_field(self) -> None:
        response = self.request("fake_model_cr_a.create", {"not_req_field": 2})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Creation of fake_model_cr_a/1: You try to set following required fields to an empty value: ['req_field']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_cr_a/1")

    def test_create_double_side(self) -> None:
        """
        2 models, that requires each other, in real life see meeting.
        Solution: fake_model_cr_b creates internally fake_model_cr_c
        """
        response = self.request("fake_model_cr_b.create", {"name": "modelB"})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "fake_model_cr_b/1", {"fake_model_cr_c_id": 1, "name": "modelB"}
        )
        self.assert_model_exists(
            "fake_model_cr_c/1", {"fake_model_cr_b_id": 1, "name": "modelC"}
        )

    def test_create_impossible_v1(self) -> None:
        """
        Try to create the other side around is not possible without internal creation
        """
        response = self.request("fake_model_cr_c.create", {"fake_model_cr_b_id": None})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Creation of fake_model_cr_c/1: You try to set following required fields to an empty value: ['fake_model_cr_b_id']",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_cr_c/1")

    def test_create_impossible_v2(self) -> None:
        response = self.request("fake_model_cr_c.create", {"fake_model_cr_b_id": 1})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. Model 'fake_model_cr_b/1' does not exist.",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_cr_c/1")
