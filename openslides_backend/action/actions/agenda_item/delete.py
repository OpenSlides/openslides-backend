from typing import Any, Dict

from ....models.models import AgendaItem
from ....permissions.permissions import Permissions
from ....shared.patterns import FullQualifiedId, string_to_fqid
from ....shared.typing import DeletedModel
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..topic.delete import TopicDelete


@register_action("agenda_item.delete")
class AgendaItemDelete(DeleteAction):
    """
    Action to delete agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_delete_schema()
    permission = Permissions.AgendaItem.CAN_MANAGE

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        fqid = FullQualifiedId(self.model.collection, instance["id"])
        agenda_item = self.datastore.get(
            fqid,
            ["content_object_id"],
        )
        if agenda_item.get("content_object_id"):
            content_object_fqid = string_to_fqid(agenda_item["content_object_id"])
            if (
                content_object_fqid.collection.collection == "topic"
                and not self.datastore.is_deleted(content_object_fqid)
            ):
                self.apply_instance(DeletedModel(), fqid)
                self.execute_other_action(
                    TopicDelete,
                    [{"id": content_object_fqid.id}],
                )
                self.apply_instance(DeletedModel(), content_object_fqid)
        return instance
