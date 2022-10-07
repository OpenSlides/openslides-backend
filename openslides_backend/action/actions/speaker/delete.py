from typing import Any, Dict

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

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        speaker = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["user_id"],
            lock_result=False,
        )
        if speaker.get("user_id") == self.user_id:
            return
        super().check_permissions(instance)
