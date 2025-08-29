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
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from openslides_backend.shared.patterns import Collection

from .base import BaseActionTestCase
from .util import create_table_view

collection_a = "fake_model_cr_a"
collection_b = "fake_model_cr_b"
collection_c = "fake_model_cr_c"
collection_d = "fake_model_cr_d"

yml = f"""
_meta:
  id_field: &id_field
    type: number
    restriction_mode: A
    constant: true
    required: true
{collection_a}:
  id: *id_field
  req_field:
    type: number
    required: true
  not_req_field:
    type: number
{collection_b}:
  id: *id_field
  name:
    type: text
  fake_model_cr_c_id:
    type: relation
    to: {collection_c}/fake_model_cr_b_id
    required: true
{collection_c}:
  id: *id_field
  name:
    type: text
  fake_model_cr_b_id:
    type: relation
    to: {collection_b}/fake_model_cr_c_id
    reference: {collection_b}
    required: true
  fake_model_cr_d_id:
    type: relation
    to: {collection_d}/fake_model_cr_c_ids
    reference: {collection_d}
{collection_d}:
  id: *id_field
  name:
    type: text
  fake_model_cr_c_ids:
    type: relation
    to: {collection_c}/fake_model_cr_d_id
    required: true
        """


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
        to={"fake_model_cr_c": "fake_model_cr_b_id"}, required=True, is_view_field=True
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
        to={"fake_model_cr_d": "fake_model_cr_c_ids"}, is_view_field=True
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
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        create_table_view(yml)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f"""
                    DROP TABLE {collection_a}_t CASCADE;
                    DROP TABLE {collection_b}_t CASCADE;
                    DROP TABLE {collection_c}_t CASCADE;
                    DROP TABLE {collection_d}_t CASCADE;
                    """
                )

    def tearDown(self) -> None:
        super().tearDown()
        with self.connection.cursor() as curs:
            curs.execute(
                f"""
                TRUNCATE TABLE {collection_a}_t RESTART IDENTITY CASCADE;
                TRUNCATE TABLE {collection_b}_t RESTART IDENTITY CASCADE;
                TRUNCATE TABLE {collection_c}_t RESTART IDENTITY CASCADE;
                TRUNCATE TABLE {collection_d}_t RESTART IDENTITY CASCADE;
                """
            )

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
            "Model 'fake_model_cr_b/1' does not exist.",
            response.json["message"],
        )
        self.assert_model_not_exists("fake_model_cr_c/1")
