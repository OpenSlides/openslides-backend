from typing import Any

from ....models.models import Speaker
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import CheckSpeechState


@register_action("speaker.update")
class SpeakerUpdate(UpdateAction, CheckSpeechState):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_update_schema(["speech_state"])
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        speaker = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["speech_state", "meeting_id"],
        )
        self.check_speech_state(speaker, instance, meeting_id=speaker["meeting_id"])
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        speaker = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_user_id", "meeting_id"],
            lock_result=False,
        )
        if speaker.get("meeting_user_id"):
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id("meeting_user", speaker["meeting_user_id"]),
                ["user_id"],
                lock_result=False,
            )
            if meeting_user.get("user_id") == self.user_id and (
                has_perm(
                    self.datastore,
                    self.user_id,
                    Permissions.ListOfSpeakers.CAN_SEE,
                    speaker["meeting_id"],
                )
                or has_perm(
                    self.datastore,
                    self.user_id,
                    Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
                    speaker["meeting_id"],
                )
            ):
                return
        super().check_permissions(instance)
