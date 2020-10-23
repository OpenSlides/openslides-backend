from typing import Iterable

from ...models.models import ListOfSpeakers
from ...shared.exceptions import ActionException
from ...shared.filters import FilterOperator
from ...shared.patterns import Collection, FullQualifiedId
from ..base import Action, ActionPayload, DataSet, WriteRequestElement
from ..default_schema import DefaultSchema
from ..register import register_action
from ..speaker.create_update_delete import SpeakerCreateAction


@register_action("list_of_speakers.re_add_last")
class ListOfSpeakersReAddLastAction(Action):
    """
    Action to re-add the last speaker to the list.
    """

    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_default_schema(
        required_properties=["id"],
        title="Re-add last speaker",
        description="Adds the last speaker as new speaker.",
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        data = []
        for instance in payload:
            list_of_speakers = self.fetch_model(
                FullQualifiedId(self.model.collection, instance["id"]),
                mapped_fields=["id", "speaker_ids"],
            )
            if not list_of_speakers.get("speaker_ids"):
                raise ActionException(
                    f"List of speakers {instance['id']} has no speakers."
                )
            filter_obj = FilterOperator("end_time", ">", 0)
            speakers = sorted(
                self.database.filter(
                    Collection("speaker"),
                    filter_obj,
                    mapped_fields=["end_time", "user_id"],
                    lock_result=True,
                ).values(),
                key=lambda speaker: speaker["end_time"],
                reverse=True,
            )
            if not speakers:
                raise ActionException("There is no last speaker that can be re-added.")
            data.append(
                {"list_of_speakers": list_of_speakers, "last_speaker": speakers[0]}
            )
        return {"data": data}

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        for element in dataset["data"]:
            action = SpeakerCreateAction(self.permission, self.database)
            yield from action.perform(
                [
                    {
                        "list_of_speakers_id": element["list_of_speakers"]["id"],
                        "user_id": element["last_speaker"]["user_id"],
                    }
                ],
                self.user_id,
            )
