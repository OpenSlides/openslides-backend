from ...models.models import ListOfSpeakers
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import UpdateAction


@register_action("list_of_speakers.update")
class ListOfSpeakersUpdateAction(UpdateAction):
    """
    Action to update a list of speakers.
    """

    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_update_schema(properties=["closed"])
