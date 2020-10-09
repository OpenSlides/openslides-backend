from time import time
from typing import Any, Dict

from ...models.models import MotionChangeRecommendation
from ..action_set import ActionSet
from ..default_schema import DefaultSchema
from ..generics import CreateAction, DeleteAction, UpdateAction
from ..register import register_action_set


class MotionChangeRecommendationCreateAction(CreateAction):
    """
    Action to create motion change recommendation
    """

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        set creation_time
        set default to type
        """
        instance["type"] = instance.get("type", 0)
        instance["creation_time"] = int(time())
        return instance


@register_action_set("motion_change_recommendation")
class MotionChangeRecommendationActionSet(ActionSet):
    """
    Actions to create, update and delete motion change_recommendations.
    """

    model = MotionChangeRecommendation()
    create_schema = DefaultSchema(MotionChangeRecommendation()).get_create_schema(
        required_properties=["line_from", "line_to", "text", "motion_id"],
        optional_properties=["rejected", "internal", "type", "other_description"],
    )
    update_schema = DefaultSchema(MotionChangeRecommendation()).get_update_schema(
        optional_properties=[
            "text",
            "rejected",
            "internal",
            "type",
            "other_description",
        ]
    )
    delete_schema = DefaultSchema(MotionChangeRecommendation()).get_delete_schema()
    routes = {
        "create": MotionChangeRecommendationCreateAction,
        "update": UpdateAction,
        "delete": DeleteAction,
    }
