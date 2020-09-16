from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.interfaces import WSGIApplication
from openslides_backend.shared.patterns import Collection
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application


class FakeModelA(Model):
    collection = Collection("fake_model_a")
    id = fields.IdField()

    # normal relations
    fake_model_b_oo = fields.OneToOneField(
        to=Collection("fake_model_b"), related_name="fake_model_a_oo"
    )
    fake_model_b_om = fields.ForeignKeyField(
        to=Collection("fake_model_b"), related_name="fake_model_a_mo"
    )
    fake_model_b_mm = fields.ManyToManyArrayField(
        to=Collection("fake_model_b"), related_name="fake_model_a_mm"
    )

    # generic relations
    fake_model_b_generic_oo = fields.OneToOneField(
        to=Collection("fake_model_b"),
        related_name="fake_model_a_generic_oo",
        generic_relation=True,
    )
    fake_model_b_generic_om = fields.ForeignKeyField(
        to=Collection("fake_model_b"),
        related_name="fake_model_a_generic_mo",
        generic_relation=True,
    )
    fake_model_b_generic_mm = fields.ManyToManyArrayField(
        to=Collection("fake_model_b"),
        related_name="fake_model_a_generic_mm",
        generic_relation=True,
    )


class FakeModelB(Model):
    collection = Collection("fake_model_b")
    id = fields.IdField()

    meeting_id = fields.RequiredForeignKeyField(
        to=Collection("meeting"), related_name="fake_model_b_ids",
    )

    # structured fields
    structured_relation_field = fields.ForeignKeyField(
        to=Collection("fake_model_a"),
        related_name="fake_model_b_$_ids",
        structured_relation=["meeting_id"],
    )


class FakeModelC(Model):
    collection = Collection("fake_model_c")
    id = fields.IdField()

    # nested structured field
    foreign_key_field = fields.ForeignKeyField(
        to=Collection("fake_model_b"), related_name="fake_model_c_ids",
    )
    structured_relation_field = fields.ForeignKeyField(
        to=Collection("fake_model_a"),
        related_name="fake_model_c_$_ids",
        structured_relation=["foreign_key_field", "meeting_id"],
    )


class BaseRelationsTestCase(BaseSystemTestCase):
    def get_application(self) -> WSGIApplication:
        return create_action_test_application()
