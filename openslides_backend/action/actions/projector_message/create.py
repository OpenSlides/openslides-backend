from ....models.models import ProjectorMessage
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector_message.create")
class ProjectorMessageCreate(CreateAction):
    """
    Action to create a projector message.
    """

    model = ProjectorMessage()
    schema = DefaultSchema(ProjectorMessage()).get_create_schema(
        required_properties=["message", "meeting_id"],
    )
