from ....models.models import MeetingMediafile
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_mediafile.delete", action_type=ActionType.BACKEND_INTERNAL)
class MeetingMediafileDelete(DeleteAction):
    """
    Action to delete a meeting mediafile.
    """

    model = MeetingMediafile()
    schema = DefaultSchema(MeetingMediafile()).get_delete_schema()
