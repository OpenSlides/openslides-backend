from ...models.models import ListOfSpeakers
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


# TODO add internal to register_action
@register_action("list_of_speakers.delete")
class ListOfSpeakersDelete(DeleteAction):
    """
    Internal action to delete a list of speakers.
    """

    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_delete_schema()
