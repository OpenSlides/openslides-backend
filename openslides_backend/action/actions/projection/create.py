from ....models.models import Projection
from ...generics.create import CreateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projection.create", action_type=ActionType.BACKEND_INTERNAL)
class ProjectionCreate(CreateAction):
    """
    Action to create a projection.
    """

    model = Projection()
    schema = DefaultSchema(Projection()).get_create_schema(
        required_properties=["content_object_id", "meeting_id"],
        optional_properties=[
            "options",
            "stable",
            "type",
            "weight",
            "current_projector_id",
            "preview_projector_id",
            "history_projector_id",
        ],
    )
