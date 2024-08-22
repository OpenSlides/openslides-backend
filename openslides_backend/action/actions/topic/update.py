from ....models.models import Topic
from ....permissions.permissions import Permissions
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..meeting_mediafile.attachment_mixin import AttachmentMixin


@register_action("topic.update")
class TopicUpdate(AttachmentMixin, UpdateAction):
    """
    Action to update simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = DefaultSchema(Topic()).get_update_schema(
        optional_properties=["title", "text", "attachment_ids"]
    )
    permission = Permissions.AgendaItem.CAN_MANAGE
