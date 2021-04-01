from ....models.models import ListOfSpeakers, Speaker
from ....permissions.permissions import Permissions
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("list_of_speakers.delete_all_speakers")
class ListOfSpeakersDeleteAllSpeakersAction(DeleteAction):
    """
    Action to delete all speakers of a list of speakers.
    """

    model = Speaker()
    schema = DefaultSchema(ListOfSpeakers()).get_default_schema(
        required_properties=["id"],
        title="Delete all speakers of list of speakers",
        description="Action to remove all speakers from the given list of speakers.",
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE
    permission_model = ListOfSpeakers()

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            list_of_speakers = self.datastore.fetch_model(
                FullQualifiedId(Collection("list_of_speakers"), instance["id"]),
                mapped_fields=["speaker_ids"],
                lock_result=True,
            )
            if list_of_speakers.get("speaker_ids"):
                yield from [
                    {"id": speaker_id} for speaker_id in list_of_speakers["speaker_ids"]
                ]
