from typing import Any, Dict

from ....models.models import AgendaItem
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

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        fqid = FullQualifiedId(self.model.collection, instance["id"])
        agenda_item = self.datastore.get(
            fqid,
            ["content_object_id"],
        )
        if agenda_item.get("content_object_id"):
            content_object_fqid = string_to_fqid(agenda_item["content_object_id"])
            if content_object_fqid.collection.collection == "topic" and not isinstance(
                self.additional_relation_models.get(content_object_fqid), DeletedModel
            ):
                self.execute_other_action(
                    TopicDelete,
                    [{"id": content_object_fqid.id}],
                    {fqid: DeletedModel()},
                )
                self.additional_relation_models[content_object_fqid] = DeletedModel()
        return instance
