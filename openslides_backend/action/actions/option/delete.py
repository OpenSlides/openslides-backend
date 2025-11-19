from typing import Any

from ....models.models import Option
from ....shared.patterns import (
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from ...generics.delete import DeleteAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..poll_candidate_list.delete import PollCandidateListDelete


@register_action("option.delete", action_type=ActionType.BACKEND_INTERNAL)
class OptionDelete(DeleteAction):
    """
    Action to delete options.
    """

    model = Option()
    schema = DefaultSchema(Option()).get_delete_schema()

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        option = self.datastore.get(
            fqid_from_collection_and_id("option", instance["id"]), ["content_object_id"]
        )
        if (
            option.get("content_object_id")
            and collection_from_fqid(option["content_object_id"])
            == "poll_candidate_list"
        ):
            self.execute_other_action(
                PollCandidateListDelete,
                [{"id": id_from_fqid(option["content_object_id"])}],
            )
        return instance
