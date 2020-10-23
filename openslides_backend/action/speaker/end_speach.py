import time
from typing import Any, Dict, Iterable

from ...models.models import Speaker
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId
from ..base import ActionPayload
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action


@register_action("speaker.end_speach")
class SpeakerEndSpeach(UpdateAction):
    """
    Action to stop speakers.
    """

    model = Speaker()
    schema = DefaultSchema(Speaker()).get_default_schema(
        required_properties=["id"],
        title="End speach schema",
        description="Schema to stop a speaker's speach.",
    )

    def get_updated_instances(self, payload: ActionPayload) -> Iterable[Dict[str, Any]]:
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
            yield instance
