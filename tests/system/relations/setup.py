from typing import Any

from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.relations.single_relation_handler import (
    SingleRelationHandler,
)
from openslides_backend.action.relations.typing import RelationFieldUpdates
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model, model_registry
from openslides_backend.shared.patterns import Collection


class FakeModelA(Model):
    collection = Collection("fake_model_a")
    verbose_name = "fake model a"

    id = fields.IntegerField()

    meeting_id = fields.RelationField(
        to={Collection("meeting"): "fake_model_a_ids"},
    )

    # normal relations
    fake_model_b_oo = fields.RelationField(
        to={Collection("fake_model_b"): "fake_model_a_oo"}
    )
    fake_model_b_om = fields.RelationField(
        to={Collection("fake_model_b"): "fake_model_a_mo"}
    )
    fake_model_b_mm = fields.RelationListField(
        to={Collection("fake_model_b"): "fake_model_a_mm"}
    )

    # generic relations
    fake_model_b_generic_oo = fields.RelationField(
        to={Collection("fake_model_b"): "fake_model_a_generic_oo"},
    )
    fake_model_b_generic_om = fields.RelationField(
        to={Collection("fake_model_b"): "fake_model_a_generic_mo"},
    )
    fake_model_b_generic_mm = fields.RelationListField(
        to={Collection("fake_model_b"): "fake_model_a_generic_mm"},
    )

    # template field / structured relation
    fake_model_b__ids = fields.TemplateRelationListField(
        replacement_collection=Collection("meeting"),
        index=13,
        to={Collection("fake_model_b"): "structured_relation_field"},
    )
    fake_model_c__ids = fields.TemplateRelationListField(
        replacement_collection=Collection("meeting"),
        index=13,
        to={Collection("fake_model_c"): "structured_relation_field"},
    )


class FakeModelB(Model):
    collection = Collection("fake_model_b")
    verbose_name = "fake model b"

    id = fields.IntegerField()

    meeting_id = fields.RelationField(
        to={Collection("meeting"): "fake_model_b_ids"},
        required=True,
    )

    fake_model_a_oo = fields.RelationField(
        to={Collection("fake_model_a"): "fake_model_b_oo"}
    )
    fake_model_a_mo = fields.RelationListField(
        to={Collection("fake_model_a"): "fake_model_b_om"}
    )
    fake_model_a_mm = fields.RelationListField(
        to={Collection("fake_model_a"): "fake_model_b_mm"}
    )
    fake_model_a_generic_oo = fields.GenericRelationField(
        to={Collection("fake_model_a"): "fake_model_b_generic_oo"},
    )
    fake_model_a_generic_mo = fields.GenericRelationListField(
        to={Collection("fake_model_a"): "fake_model_b_generic_om"},
    )
    fake_model_a_generic_mm = fields.GenericRelationListField(
        to={Collection("fake_model_a"): "fake_model_b_generic_mm"},
    )

    structured_relation_field = fields.RelationField(
        to={Collection("fake_model_a"): "fake_model_b_$_ids"},
    )

    fake_model_c_ids = fields.RelationListField(
        to={Collection("fake_model_c"): "foreign_key_field"},
    )


class FakeModelC(Model):
    collection = Collection("fake_model_c")
    verbose_name = "fake model c"

    id = fields.IntegerField()

    meeting_id = fields.RelationField(
        to={Collection("meeting"): "fake_model_b_ids"},
        required=True,
    )

    # nested structured field
    foreign_key_field = fields.RelationField(
        to={Collection("fake_model_b"): "fake_model_c_ids"},
    )
    structured_relation_field = fields.RelationField(
        to={Collection("fake_model_a"): "fake_model_c_$_ids"},
    )


@register_action("fake_model_a.create", internal=True)
class FakeModelACreateAction(CreateAction):
    model = FakeModelA()
    schema = {}  # type: ignore


@register_action("fake_model_a.update", internal=True)
class FakeModelAUpdateAction(UpdateAction):
    model = FakeModelA()
    schema = {}  # type: ignore


class SingleRelationHandlerWithContext(SingleRelationHandler):
    """
    Overwrites the perform method of the SingleRelationHandler to provide a datastore context.
    """

    def perform(self) -> RelationFieldUpdates:
        with self.datastore.get_database_context():
            return super().perform()


def assure_model_in_registry(model: Any) -> None:
    collection = model.collection
    if collection not in model_registry:
        model_registry[collection] = model
