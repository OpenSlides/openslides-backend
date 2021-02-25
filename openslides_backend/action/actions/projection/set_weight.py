from ....models.models import Projection
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projection.set_weight", internal=True)
class ProjectionSetWeight(UpdateAction):
    """
    Internal action to set the weight of a projection.
    """

    model = Projection()
    schema = DefaultSchema(Projection()).get_update_schema(
        required_properties=["weight"]
    )
