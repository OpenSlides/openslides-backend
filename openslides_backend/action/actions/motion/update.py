import time
from typing import Any, Dict

from ....models.models import Motion
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .amendment_paragraphs_mixin import (
    AmendmentParagraphsMixin,
    amendment_paragraphs_schema,
)


@register_action("motion.update")
class MotionUpdate(UpdateAction, AmendmentParagraphsMixin):
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
            "modified_final_version",
        ],
        additional_optional_fields={
            "amendment_paragraphs": amendment_paragraphs_schema
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["last_modified"] = round(time.time())
        self.handle_amendment_paragraphs(instance)
        return instance
