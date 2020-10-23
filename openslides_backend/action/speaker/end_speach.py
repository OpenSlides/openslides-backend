import time
from typing import Iterable

from ...models.models import Speaker
from ...shared.exceptions import ActionException
from ...shared.interfaces import Event
from ...shared.patterns import FullQualifiedId
from ..base import Action, ActionPayload, DataSet, WriteRequestElement
from ..default_schema import DefaultSchema
from ..register import register_action


@register_action("speaker.end_speach")
class SpeakerEndSpeach(Action):
    """
    Action to stop speakers.
    """

    model = Speaker()
    schema = DefaultSchema(Speaker()).get_default_schema(
        required_properties=["id"],
        title="End speach schema",
        description="Schema to stop a speaker's speach.",
    )

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        data = []
        for instance in payload:
            speaker = self.fetch_model(
                FullQualifiedId(self.model.collection, instance["id"]),
                mapped_fields=["begin_time", "end_time"],
            )
            if speaker.get("begin_time") is None or speaker.get("end_time") is not None:
                raise ActionException(
                    f"Speaker {instance['id']} is not speaking at the moment."
                )
            instance["end_time"] = round(time.time())
            data.append({"instance": instance})
        return {"data": data}

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        for element in dataset["data"]:
            fqid = FullQualifiedId(self.model.collection, element["instance"]["id"])
            information = {fqid: ["Object updated"]}
            fields = {k: v for k, v in element["instance"].items() if k != "id"}
            event = Event(type="update", fqid=fqid, fields=fields)
            yield WriteRequestElement(
                events=[event], information=information, user_id=self.user_id
            )
