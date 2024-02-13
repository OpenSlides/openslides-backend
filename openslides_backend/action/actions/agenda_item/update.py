from ....models.models import AgendaItem
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .permission_mixin import AgendaItemPermissionMixin


@register_action("agenda_item.update")
class AgendaItemUpdate(AgendaItemPermissionMixin, UpdateAction):
    """
    Action to update agenda items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_update_schema(
        optional_properties=[
            "item_number",
            "comment",
            "closed",
            "type",
            "weight",
            "tag_ids",
            "duration",
            "moderator_notes",
        ]
    )
    permission = Permissions.AgendaItem.CAN_MANAGE

    def calc_is_internal(
        self, type_: int | None, parent_is_internal: bool | None
    ) -> bool:
        return type_ == AgendaItem.INTERNAL_ITEM or bool(parent_is_internal)

    def calc_is_hidden(self, type_: int | None, parent_is_hidden: bool | None) -> bool:
        return type_ == AgendaItem.HIDDEN_ITEM or bool(parent_is_hidden)

    def handle_children(
        self, id_: int, parent_is_hidden: bool, parent_is_internal: bool
    ) -> ActionData:
        instances = []
        agenda_item = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, id_), ["child_ids"]
        )
        if agenda_item.get("child_ids"):
            get_many_request = GetManyRequest(
                self.model.collection,
                agenda_item["child_ids"],
                ["type", "is_hidden", "is_internal"],
            )
            gm_result = self.datastore.get_many([get_many_request])
            children = gm_result.get(self.model.collection, {})
            for child_id in children:
                child_ai = children[child_id]
                instance = dict()
                instance["id"] = child_id
                instance["is_hidden"] = self.calc_is_hidden(
                    child_ai.get("type"), parent_is_hidden
                )
                instance["is_internal"] = self.calc_is_internal(
                    child_ai.get("type"), parent_is_internal
                )
                if (
                    child_ai.get("is_hidden") == instance["is_hidden"]
                    and child_ai.get("is_internal") == instance["is_internal"]
                ):
                    continue
                instances.append(instance)
                self.apply_instance(instance)
                instances.extend(
                    self.handle_children(
                        child_id,
                        bool(instance["is_hidden"]),
                        bool(instance["is_internal"]),
                    )
                )
        return instances

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        new_instances = []
        agenda_item_ids = [instance["id"] for instance in action_data]
        get_many_request = GetManyRequest(
            self.model.collection, agenda_item_ids, ["parent_id", "child_ids"]
        )

        gm_result = self.datastore.get_many([get_many_request])
        agenda_items = gm_result.get(self.model.collection, {})

        for instance in action_data:
            if instance.get("type") is None:
                new_instances.append(instance)
                continue
            agenda_item = agenda_items[instance["id"]]
            if agenda_item.get("parent_id"):
                parent_ai = self.datastore.get(
                    fqid_from_collection_and_id(
                        self.model.collection, agenda_item["parent_id"]
                    ),
                    ["is_hidden", "is_internal"],
                )
            else:
                parent_ai = {"is_hidden": False, "is_internal": False}
            instance["is_hidden"] = self.calc_is_hidden(
                instance["type"], parent_ai.get("is_hidden")
            )
            instance["is_internal"] = self.calc_is_internal(
                instance["type"], parent_ai.get("is_internal")
            )
            new_instances.append(instance)
            self.apply_instance(instance)
            new_instances.extend(
                self.handle_children(
                    instance["id"], instance["is_hidden"], instance["is_internal"]
                )
            )
        return new_instances
