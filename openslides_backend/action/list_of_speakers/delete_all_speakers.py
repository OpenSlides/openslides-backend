from typing import Iterable, Union

from ...models.models import ListOfSpeakers
from ...shared.patterns import FullQualifiedId
from ..action_interface import ActionResponseResultsElement
from ..base import Action, ActionPayload, DataSet, WriteRequestElement
from ..default_schema import DefaultSchema
from ..register import register_action
from ..speaker.create_update_delete import SpeakerDeleteAction


@register_action("list_of_speakers.delete_all_speakers")
class ListOfSpeakersDeleteAllSpeakersAction(Action):
    """
    Action to delete all speakers of a list of speakers.
    """

    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_default_schema(
        required_properties=["id"],
        title="Delete all speakers of list of speakers",
        description="Action to remove all speakers from the given list of speakers.",
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        data = []
        for instance in payload:
            list_of_speakers = self.fetch_model(
                FullQualifiedId(self.model.collection, instance["id"]),
                mapped_fields=["speaker_ids"],
            )
            if not list_of_speakers.get("speaker_ids"):
                continue
            data.append(list_of_speakers)
        return {"data": data}

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        for element in dataset["data"]:
            payload = [{"id": speaker_id} for speaker_id in element["speaker_ids"]]
            yield from self.execute_other_action(SpeakerDeleteAction, payload)
