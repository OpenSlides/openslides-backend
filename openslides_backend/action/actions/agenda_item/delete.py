from typing import Any

from ....models.models import AgendaItem
from ....permissions.permissions import Permissions
from ....shared.patterns import (
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
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

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """Deletes the topic before the relation handling can try to create a faulty update to it."""
        fqid = fqid_from_collection_and_id(self.model.collection, instance["id"])
        agenda_item = self.datastore.get(
            fqid,
            ["content_object_id"],
        )
        if content_object_fqid := agenda_item.get("content_object_id"):
            if collection_from_fqid(
                content_object_fqid
            ) == "topic" and not self.datastore.is_to_be_deleted(content_object_fqid):
                self.execute_other_action(
                    TopicDelete,
                    [{"id": id_from_fqid(content_object_fqid)}],
                )
        return instance
