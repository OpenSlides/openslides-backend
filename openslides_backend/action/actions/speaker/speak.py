import time

from ....models.models import Speaker
from ....services.datastore.deleted_models_behaviour import InstanceAdditionalBehaviour
from ....services.datastore.interface import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("speaker.speak")
class SpeakerSpeak(UpdateAction):
    """
    Action to let speakers speak.
    """

    model = Speaker()
    schema = DefaultSchema(Speaker()).get_default_schema(
        required_properties=["id"],
        title="Speak schema",
        description="Schema to let a speaker's speach begin.",
    )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            this_speaker = self.datastore.fetch_model(
                FullQualifiedId(self.model.collection, instance["id"]),
                mapped_fields=["list_of_speakers_id"],
                db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
                lock_result=True,
            )
            list_of_speakers = self.datastore.fetch_model(
                FullQualifiedId(
                    Collection("list_of_speakers"), this_speaker["list_of_speakers_id"]
                ),
                mapped_fields=["speaker_ids", "closed"],
                db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
                lock_result=True,
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
                    # stop current speaker
                    yield {
                        "id": speaker_id,
                        "end_time": now,
                    }
            yield instance
