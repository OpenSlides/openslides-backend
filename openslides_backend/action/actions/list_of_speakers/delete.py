from ....models.models import ListOfSpeakers
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("list_of_speakers.delete", action_type=ActionType.BACKEND_INTERNAL)
class ListOfSpeakersDelete(DeleteAction):
    """
    Internal action to delete a list of speakers.
    """

    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_delete_schema()
