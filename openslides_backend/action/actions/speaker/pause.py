from time import time
from typing import Any

from openslides_backend.action.mixins.singular_action_mixin import SingularActionMixin

from ....models.models import Speaker
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..projector_countdown.mixins import CountdownCommand, CountdownControl


@register_action("speaker.pause")
class SpeakerPause(SingularActionMixin, CountdownControl, UpdateAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_default_schema(
        required_properties=["id"],
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        db_instance = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [
                "begin_time",
                "end_time",
                "pause_time",
                "unpause_time",
                "speech_state",
                "meeting_id",
                "structure_level_list_of_speakers_id",
                "point_of_order",
            ],
        )
        if (
            db_instance.get("begin_time") is None
            or db_instance.get("end_time") is not None
            or db_instance.get("pause_time") is not None
        ):
            raise ActionException("Speaker is not currently speaking.")

        instance["pause_time"] = now = round(time())

        # update countdowns
        self.decrease_structure_level_countdown(now, db_instance)
        self.control_los_countdown(db_instance["meeting_id"], CountdownCommand.STOP)
        return instance
