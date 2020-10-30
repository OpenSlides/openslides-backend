import time
from typing import Any, Dict

from ...models.models import Motion
from ..base import DummyAction
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
        optional_properties=[
            "title",
            "number",
            "text",
            "reason",
            "amendment_paragraph_",
            "modified_final_version",
        ]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["last_modified"] = round(time.time())
        return instance


@register_action("motion.support")
class MotionSupport(DummyAction):
    # TODO: Support and unsupport
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
