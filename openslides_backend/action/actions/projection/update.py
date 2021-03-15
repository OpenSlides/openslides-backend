from ....models.models import Projection
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projection.update", internal=True)
class ProjectionUpdate(UpdateAction):
    """
    Action to update a projection.
    """

    model = Projection()
    schema = DefaultSchema(Projection()).get_update_schema(
        optional_properties=[
            "current_projector_id",
            "history_projector_id",
            "preview_projector_id",
            "weight",
        ]
    )
