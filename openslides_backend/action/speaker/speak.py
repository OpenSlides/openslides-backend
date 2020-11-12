import time
from typing import Iterable, Union

from ...models.models import Speaker
from ...services.datastore.interface import GetManyRequest
from ...shared.exceptions import ActionException
from ...shared.interfaces.event import Event
from ...shared.patterns import Collection, FullQualifiedId
from ..action_interface import ActionResponseResultsElement
from ..base import Action, ActionPayload, DataSet, WriteRequestElement
from ..default_schema import DefaultSchema
from ..register import register_action


@register_action("speaker.speak")
class SpeakerSpeak(Action):
    """
    Action to let speakers speak.
    """

    model = Speaker()
    schema = DefaultSchema(Speaker()).get_default_schema(
        required_properties=["id"],
        title="Speak schema",
        description="Schema to let a speaker's speach begin.",
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        data = []
        for instance in payload:
            this_speaker = self.fetch_model(
                FullQualifiedId(self.model.collection, instance["id"]),
                mapped_fields=["list_of_speakers_id"],
            )
            list_of_speakers = self.fetch_model(
                FullQualifiedId(
                    Collection("list_of_speakers"), this_speaker["list_of_speakers_id"]
                ),
                mapped_fields=["speaker_ids", "closed"],
            )
            if list_of_speakers.get("closed"):
                raise ActionException("The list of speakers is closed.")
            gmr = GetManyRequest(
                self.model.collection,
                list_of_speakers["speaker_ids"],
                ["begin_time", "end_time"],
            )
            speakers = self.datastore.get_many([gmr])
            now = round(time.time())
            current_speaker = None
            for speaker_id, speaker in speakers[self.model.collection].items():
                if speaker_id == instance["id"]:
                    if speaker.get("begin_time") is not None:
                        raise ActionException("Speaker has already started to speak.")
                    assert speaker.get("end_time") is None
                    instance["begin_time"] = now
                    continue
                if (
                    speaker.get("begin_time") is not None
                    and speaker.get("end_time") is None
                ):
                    assert current_speaker is None
                    current_speaker = {
                        "id": speaker_id,
                        "end_time": now,
                    }
            data.append({"instance": instance, "current_speaker": current_speaker})
        return {"data": data}

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        for element in dataset["data"]:
            for item in ("instance", "current_speaker"):
                if element.get(item):
                    fqid = FullQualifiedId(self.model.collection, element[item]["id"])
                    information = {fqid: ["Object updated"]}
                    fields = {k: v for k, v in element[item].items() if k != "id"}
                    event = Event(type="update", fqid=fqid, fields=fields)
                    yield WriteRequestElement(
                        events=[event], information=information, user_id=self.user_id
                    )
