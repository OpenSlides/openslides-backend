from ....models.models import AgendaItem
from ....permissions.permissions import Permissions
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
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
        meeting_id = instance["meeting_id"]
        agenda_items = self.datastore.filter(
            collection=self.model.collection,
            filter=FilterOperator("meeting_id", "=", meeting_id),
            mapped_fields=["id", "item_number", "parent_id", "weight", "type"],
        )

        # Build agenda tree and get new numbers
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id),
            ["agenda_numeral_system", "agenda_number_prefix"],
        )
        numeral_system = meeting.get("agenda_numeral_system", "arabic")
        agenda_number_prefix = meeting.get("agenda_number_prefix")
        result = AgendaTree(agenda_items.values()).number_all(
            numeral_system=numeral_system, agenda_number_prefix=agenda_number_prefix
        )
        return [{"id": key, "item_number": val} for key, val in result.items()]
