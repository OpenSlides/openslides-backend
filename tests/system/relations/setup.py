from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.relations.single_relation_handler import (
    SingleRelationHandler,
)
from openslides_backend.action.relations.typing import RelationFieldUpdates
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model


class FakeModelA(Model):
    collection = "fake_model_a"
    verbose_name = "fake model a"

    id = fields.IntegerField()

    meeting_id = fields.RelationField(
        to={"meeting": "fake_model_a_ids"},
    )

    # normal relations
    fake_model_b_oo = fields.RelationField(to={"fake_model_b": "fake_model_a_oo"})
    fake_model_b_om = fields.RelationField(to={"fake_model_b": "fake_model_a_mo"})
    fake_model_b_mm = fields.RelationListField(to={"fake_model_b": "fake_model_a_mm"})

    # generic relations
    fake_model_b_generic_oo = fields.RelationField(
        to={"fake_model_b": "fake_model_a_generic_oo"},
    )
    fake_model_b_generic_om = fields.RelationField(
        to={"fake_model_b": "fake_model_a_generic_mo"},
    )
    fake_model_b_generic_mm = fields.RelationListField(
        to={"fake_model_b": "fake_model_a_generic_mm"},
    )
    # generic field which is m2m in one target collection and m2o in another
    # Important: First comes the m2o relation
    fake_model_generic_multitype = fields.GenericRelationField(
        to={
            "fake_model_c": "fake_model_a_generic_multitype_o",
            "fake_model_b": "fake_model_a_generic_multitype_m",
        },
    )


class FakeModelB(Model):
    collection = "fake_model_b"
    verbose_name = "fake model b"

    id = fields.IntegerField()

    meeting_id = fields.RelationField(
        to={"meeting": "fake_model_b_ids"},
        required=True,
    )

    fake_model_a_oo = fields.RelationField(to={"fake_model_a": "fake_model_b_oo"})
    fake_model_a_mo = fields.RelationListField(to={"fake_model_a": "fake_model_b_om"})
    fake_model_a_mm = fields.RelationListField(to={"fake_model_a": "fake_model_b_mm"})
    fake_model_a_generic_oo = fields.GenericRelationField(
        to={"fake_model_a": "fake_model_b_generic_oo"},
    )
    fake_model_a_generic_mo = fields.GenericRelationListField(
        to={"fake_model_a": "fake_model_b_generic_om"},
    )
    fake_model_a_generic_mm = fields.GenericRelationListField(
        to={"fake_model_a": "fake_model_b_generic_mm"},
    )
    fake_model_a_generic_multitype_m = fields.RelationListField(
        to={"fake_model_a": "fake_model_generic_multitype"},
    )
    fake_model_c_ids = fields.RelationListField(
        to={"fake_model_c": "foreign_key_field"},
    )


class FakeModelC(Model):
    collection = "fake_model_c"
    verbose_name = "fake model c"

    id = fields.IntegerField()

    meeting_id = fields.RelationField(
        to={"meeting": "fake_model_b_ids"},
        required=True,
    )

    fake_model_a_generic_multitype_o = fields.RelationField(
        to={"fake_model_a": "fake_model_generic_multitype"},
    )

    foreign_key_field = fields.RelationField(
        to={"fake_model_b": "fake_model_c_ids"},
    )


@register_action("fake_model_a.create", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelACreateAction(CreateAction):
    model = FakeModelA()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_a.update", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelAUpdateAction(UpdateAction):
    model = FakeModelA()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


class SingleRelationHandlerWithContext(SingleRelationHandler):
    """
    Overwrites the perform method of the SingleRelationHandler to provide a datastore context.
    """

    def perform(self) -> RelationFieldUpdates:
        with self.datastore.get_database_context():
            return super().perform()
