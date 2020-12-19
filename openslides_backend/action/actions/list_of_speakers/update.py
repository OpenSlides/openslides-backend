from ....models.models import ListOfSpeakers
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("list_of_speakers.update")
class ListOfSpeakersUpdateAction(UpdateAction):
    """
    Action to update a list of speakers.
    """

    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_update_schema(
        optional_properties=["closed"]
    )
    permission_description = "agenda.can_manage_list_of_speakers"
