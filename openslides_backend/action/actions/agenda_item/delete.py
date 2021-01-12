from typing import Any, Dict

from ....models.models import AgendaItem
from ....shared.patterns import KEYSEPARATOR, FullQualifiedId
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        agenda_item = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]),
            ["content_object_id"],
        )
        if agenda_item.get("content_object_id") and agenda_item[
            "content_object_id"
        ].startswith("topic" + KEYSEPARATOR):
            _, id_ = agenda_item["content_object_id"].split(KEYSEPARATOR)
            self.execute_other_action(TopicDelete, [{"id": int(id_)}])
        return instance
