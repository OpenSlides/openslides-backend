import time

from ...models.models import Motion
from ..base import ActionPayload, DataSet, DummyAction
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("motion.update")
class MotionUpdate(UpdateAction):
    """
    Action to update motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(
        optional_properties=["title", "statute_paragraph_id"]
    )  # TODO number, modified_final_version, reason, text, amendmend_paragraphs, lead_motion_id, attachment_ids

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        for instance in payload:
            instance["last_modified"] = round(time.time())
        return super().prepare_dataset(payload)


@register_action("motion.support")
class MotionSupport(DummyAction):
    # TODO: Support and unsupport
    pass


@register_action("motion.follow_recommendation")
class MotionFollowRecommendation(DummyAction):
    pass


@register_action("motion.manage_comments")
class MotionManageComments(DummyAction):
    pass


@register_action("motion.numbering_in_category")
class MotionNumberingInCategory(DummyAction):
    pass


@register_action("motion.create_poll")
class MotionCreatePoll(DummyAction):
    pass
