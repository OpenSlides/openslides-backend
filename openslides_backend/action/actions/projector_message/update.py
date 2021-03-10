from ....models.models import ProjectorMessage
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector_message.update")
class ProjectorMessageUpdate(UpdateAction):
    """
    Action to update a projector message.
    """

    model = ProjectorMessage()
    schema = DefaultSchema(ProjectorMessage()).get_update_schema(
        optional_properties=["message"],
    )
