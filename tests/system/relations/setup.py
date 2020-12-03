from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.util import (  # noqa  Important to prevent circular imports
    actions_map,
)
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from openslides_backend.shared.patterns import Collection
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application


class FakeModelA(Model):
    collection = Collection("fake_model_a")
    verbose_name = "fake model a"

    id = fields.IntegerField()

    # normal relations
    fake_model_b_oo = fields.RelationField(
        to=Collection("fake_model_b"), related_name="fake_model_a_oo"
    )
    fake_model_b_om = fields.RelationField(
        to=Collection("fake_model_b"), related_name="fake_model_a_mo"
    )
    fake_model_b_mm = fields.RelationListField(
        to=Collection("fake_model_b"), related_name="fake_model_a_mm"
    )

    # generic relations
    fake_model_b_generic_oo = fields.RelationField(
        to=Collection("fake_model_b"),
        related_name="fake_model_a_generic_oo",
        generic_relation=True,
    )
    fake_model_b_generic_om = fields.RelationField(
        to=Collection("fake_model_b"),
        related_name="fake_model_a_generic_mo",
        generic_relation=True,
    )
    fake_model_b_generic_mm = fields.RelationListField(
        to=Collection("fake_model_b"),
        related_name="fake_model_a_generic_mm",
        generic_relation=True,
    )

    # template field / structured relation
    fake_model_b__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=13,
        to=Collection("fake_model_b"),
        related_name="structured_relation_field",
    )
    fake_model_c__ids = fields.TemplateRelationListField(
        replacement="meeting_id",
        index=13,
        to=Collection("fake_model_c"),
        related_name="structured_relation_field",
    )


class FakeModelB(Model):
    collection = Collection("fake_model_b")
    verbose_name = "fake model b"

    id = fields.IntegerField()

    meeting_id = fields.RelationField(
        to=Collection("meeting"),
        related_name="fake_model_b_ids",
        required=True,
    )

    fake_model_a_oo = fields.RelationField(
        to=Collection("fake_model_a"), related_name="fake_model_b_oo"
    )
    fake_model_a_mo = fields.RelationListField(
        to=Collection("fake_model_a"), related_name="fake_model_b_om"
    )
    fake_model_a_mm = fields.RelationListField(
        to=Collection("fake_model_a"), related_name="fake_model_b_mm"
    )
    fake_model_a_generic_oo = fields.GenericRelationField(
        to=[Collection("fake_model_a")],
        related_name="fake_model_b_generic_oo",
    )
    fake_model_a_generic_mo = fields.GenericRelationListField(
        to=[Collection("fake_model_a")],
        related_name="fake_model_b_generic_om",
    )
    fake_model_a_generic_mm = fields.GenericRelationListField(
        to=[Collection("fake_model_a")],
        related_name="fake_model_b_generic_mm",
    )

    structured_relation_field = fields.RelationField(
        to=Collection("fake_model_a"),
        related_name="fake_model_b_$_ids",
        structured_relation=["meeting_id"],
    )

    fake_model_c_ids = fields.RelationListField(
        to=Collection("fake_model_c"),
        related_name="foreign_key_field",
    )


class FakeModelC(Model):
    collection = Collection("fake_model_c")
    verbose_name = "fake model c"

    id = fields.IntegerField()

    # nested structured field
    foreign_key_field = fields.RelationField(
        to=Collection("fake_model_b"),
        related_name="fake_model_c_ids",
    )
    structured_relation_field = fields.RelationField(
        to=Collection("fake_model_a"),
        related_name="fake_model_c_$_ids",
        structured_relation=["foreign_key_field", "meeting_id"],
    )


@register_action("fake_model_a.create")
class FakeModelACreateAction(CreateAction):
    model = FakeModelA()
    schema = {}  # type: ignore


@register_action("fake_model_a.update")
class FakeModelAUpdateAction(UpdateAction):
    model = FakeModelA()
    schema = {}  # type: ignore


class BaseRelationsTestCase(BaseSystemTestCase):
    def get_application(self) -> WSGIApplication:
        return create_action_test_application()
