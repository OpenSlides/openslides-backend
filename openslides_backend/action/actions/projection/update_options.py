from ....models.models import Projection
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projection.update_options")
class ProjectionUpdateOptions(UpdateAction):
    """
    Action to update the options of a projection.
    """

    model = Projection()
    schema = DefaultSchema(Projection()).get_update_schema(
        required_properties=["options"]
    )
    permission = Permissions.Projector.CAN_MANAGE
