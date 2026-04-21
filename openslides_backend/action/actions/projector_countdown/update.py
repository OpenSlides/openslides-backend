from ....models.models import ProjectorCountdown
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector_countdown.update")
class ProjectorCountdownUpdate(UpdateAction):
    """
    Action to update a projector countdown.
    """

    model = ProjectorCountdown()
    schema = DefaultSchema(ProjectorCountdown()).get_update_schema(
        required_properties=[],
        optional_properties=[
            "title",
            "description",
            "default_time",
            "countdown_time",
            "running",
        ],
    )
    permission = Permissions.Projector.CAN_MANAGE
