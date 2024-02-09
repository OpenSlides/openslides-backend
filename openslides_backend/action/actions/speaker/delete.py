from typing import Any

from ....models.models import Speaker
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("speaker.delete")
class SpeakerDeleteAction(DeleteAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_delete_schema()
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def check_permissions(self, instance: dict[str, Any]) -> None:
        speaker = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_user_id"],
            lock_result=False,
        )
        if speaker.get("meeting_user_id"):
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id("meeting_user", speaker["meeting_user_id"]),
                ["user_id"],
            )

            if meeting_user.get("user_id") == self.user_id:
                return
        super().check_permissions(instance)
