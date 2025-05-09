from ....models.models import AgendaItem
from ....permissions.permissions import Permissions
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


@register_action("agenda_item.assign")
class AgendaItemAssign(UpdateAction, SingularActionMixin):
    """
    Action to assign agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_default_schema(
        title="Agenda items assign new parent schema",
        description="An object containing an array of agenda item ids and the new parent id the items should be assigned to.",
        required_properties=["parent_id", "meeting_id"],
        additional_required_fields={
            "ids": {
                "description": "An array of agenda item ids where the items should be assigned to the new parent id.",
                **id_list_schema,
            }
        },
    )
    permission = Permissions.AgendaItem.CAN_MANAGE

    def prefetch(self, action_data: ActionData) -> None:
        assign_item_ids = set()
        for instance in action_data:
            if instance.get("parent_id"):
                assign_item_ids.add(instance["parent_id"])
            if instance.get("ids"):
                assign_item_ids.update(instance["ids"])

        self.datastore.get_many(
            [
                GetManyRequest(
                    "agenda_item",
                    list(assign_item_ids),
                    ["parent_id", "child_ids", "meeting_id", "weight", "level"],
                )
            ]
        )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.prepare_assign_data(
            parent_id=instance["parent_id"],
            ids=instance["ids"],
            meeting_id=instance["meeting_id"],
        )

    def prepare_assign_data(
        self, parent_id: int | None, ids: list[int], meeting_id: int
    ) -> ActionData:
        filter = FilterOperator("meeting_id", "=", meeting_id)
        db_instances = self.datastore.filter(
            collection=self.model.collection,
            filter=filter,
            mapped_fields=["id"],
        )

        ancesters = []
        if parent_id:
            # Calculate the ancesters of parent
            ancesters.append(parent_id)
            grandparent = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, parent_id),
                ["parent_id"],
            )
            while grandparent.get("parent_id") is not None:
                gp_parent_id = grandparent["parent_id"]
                ancesters.append(gp_parent_id)
                grandparent = self.datastore.get(
                    fqid_from_collection_and_id(self.model.collection, gp_parent_id),
                    ["parent_id"],
                )
        for num, id_ in enumerate(ids):
            if id_ in ancesters:
                raise ActionException(
                    f"Assigning item {id_} to one of its children is not possible."
                )
            if id_ not in db_instances:
                raise ActionException(f"Id {id_} not in db_instances.")
            if parent_id:
                parent = self.datastore.get(
                    fqid_from_collection_and_id(self.model.collection, parent_id),
                    ["weight", "level"],
                )
                new_weight = parent.get("weight", 0) + 1 + num
                new_level = parent.get("level", 0) + 1
            else:
                new_weight = 10000 + num
                new_level = 0

            yield {
                "id": id_,
                "parent_id": parent_id,
                "weight": new_weight,
                "level": new_level,
            }
