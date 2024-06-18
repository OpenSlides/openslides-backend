from openslides_backend.services.datastore.commands import GetManyRequest

from ....models.models import AgendaItem
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .agenda_tree import AgendaTree


@register_action("agenda_item.numbering")
class AgendaItemNumbering(SingularActionMixin, UpdateAction):
    """
    Action to number all public agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_default_schema(["meeting_id"])
    permission = Permissions.AgendaItem.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Fetch all agenda items for this meeting from datastore.
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))

        # Fetch data
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            ["agenda_item_ids", "agenda_numeral_system", "agenda_number_prefix"],
        )
        agenda_items = self.datastore.get_many(
            [
                GetManyRequest(
                    "agenda_item",
                    meeting.get("agenda_item_ids", []),
                    ["id", "item_number", "parent_id", "weight", "type"],
                )
            ]
        ).get("agenda_item", {})
        numeral_system = meeting.get("agenda_numeral_system", "arabic")
        agenda_number_prefix = meeting.get("agenda_number_prefix")
        # Build agenda tree and get new numbers
        result = AgendaTree(agenda_items.values()).number_all(
            numeral_system, agenda_number_prefix
        )
        return [{"id": key, "item_number": val} for key, val in result.items()]
