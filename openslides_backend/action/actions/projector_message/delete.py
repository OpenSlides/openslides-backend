from ....models.models import ProjectorMessage
from ....permissions.permissions import Permissions
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector_message.delete")
class ProjectorMessageDelete(DeleteAction):
    """
    Action to delete a projector message.
    """

    model = ProjectorMessage()
    schema = DefaultSchema(ProjectorMessage()).get_delete_schema()
    permission = Permissions.Projector.CAN_MANAGE
