from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model

from .base import BaseActionTestCase


class FakeModelURA(Model):
    collection = "fake_model_ur_a"
    verbose_name = "fake model for cascade update a"
    id = fields.IntegerField()

    fake_model_ur_b_id = fields.RelationField(
        to={"fake_model_ur_b": "fake_model_ur_a_id"},
    )
    fake_model_ur_b_required_id = fields.RelationField(
        to={"fake_model_ur_b": "fake_model_ur_a_required_id"},
    )


class FakeModelURB(Model):
    collection = "fake_model_ur_b"
    verbose_name = "fake model for cascade update b"
    id = fields.IntegerField()

    fake_model_ur_a_id = fields.RelationField(
        to={"fake_model_ur_a": "fake_model_ur_b_id"},
    )
    fake_model_ur_a_required_id = fields.RelationField(
        to={"fake_model_ur_a": "fake_model_ur_b_required_id"},
        required=True,
    )


@register_action("fake_model_ur_a.update", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelURAUpdateAction(UpdateAction):
    model = FakeModelURA()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


class TestUpdateRelation(BaseActionTestCase):
    def test_set_to_null(self) -> None:
        self.set_models(
            {
                "fake_model_ur_a/1": {"fake_model_ur_b_id": 1},
                "fake_model_ur_b/1": {"fake_model_ur_a_id": 1},
            }
        )
        response = self.request(
            "fake_model_ur_a.update", {"id": 1, "fake_model_ur_b_id": None}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_ur_a/1", {"fake_model_ur_b_id": None})
        self.assert_model_exists("fake_model_ur_b/1", {"fake_model_ur_a_id": None})

    def test_set_required_to_null(self) -> None:
        self.set_models(
            {
                "fake_model_ur_a/1": {"fake_model_ur_b_required_id": 1},
                "fake_model_ur_b/1": {"fake_model_ur_a_required_id": 1},
            }
        )
        response = self.request(
            "fake_model_ur_a.update", {"id": 1, "fake_model_ur_b_required_id": None}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Update of fake_model_ur_b/1: You try to set following required fields to an empty value: ['fake_model_ur_a_required_id']",
            response.json["message"],
        )
        self.assert_model_exists(
            "fake_model_ur_a/1", {"fake_model_ur_b_required_id": 1}
        )
        self.assert_model_exists(
            "fake_model_ur_b/1", {"fake_model_ur_a_required_id": 1}
        )

    def test_set_required_to_0(self) -> None:
        self.set_models(
            {
                "fake_model_ur_a/1": {"fake_model_ur_b_required_id": 1},
                "fake_model_ur_b/1": {"fake_model_ur_a_required_id": 1},
            }
        )
        response = self.request(
            "fake_model_ur_a.update", {"id": 1, "fake_model_ur_b_required_id": 0}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Update of fake_model_ur_b/1: You try to set following required fields to an empty value: ['fake_model_ur_a_required_id']",
            response.json["message"],
        )
        self.assert_model_exists(
            "fake_model_ur_a/1", {"fake_model_ur_b_required_id": 1}
        )
        self.assert_model_exists(
            "fake_model_ur_b/1", {"fake_model_ur_a_required_id": 1}
        )
