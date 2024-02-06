from typing import Any

from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .calculate_mixins import (
    MediafileCalculatedFieldsMixin,
    calculate_inherited_groups_helper_with_parent_id,
)
from .mixins import MediafileMixin


@register_action("mediafile.move")
class MediafileMoveAction(
    MediafileMixin,
    UpdateAction,
    SingularActionMixin,
    MediafileCalculatedFieldsMixin,
):
    """
    Action to move mediafiles.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_default_schema(
        title="Mediafile new parent schema",
        description="An object containing an array of mediafile ids and the new parent id the items should be moved to.",
        required_properties=["parent_id", "owner_id"],
        additional_required_fields={
            "ids": {
                "description": "An array of agenda item ids where the items should be assigned to the new parent id.",
                **id_list_schema,
            }
        },
    )
    permission = Permissions.Mediafile.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        yield from self.prepare_move_data(
            parent_id=instance["parent_id"],
            ids=instance["ids"],
            owner_id=instance["owner_id"],
        )

    def prepare_move_data(
        self, parent_id: int | None, ids: list[int], owner_id: str
    ) -> ActionData:
        get_many_request = GetManyRequest(
            self.model.collection, ids, ["owner_id", "access_group_ids"]
        )
        gm_result = self.datastore.get_many([get_many_request])
        db_instances = gm_result.get(self.model.collection, {})

        if parent_id is not None:
            # Calculate the ancesters of parent
            ancesters = [parent_id]
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
            for id_ in ids:
                if id_ in ancesters:
                    raise ActionException(
                        f"Moving item {id_} to one of its children is not possible."
                    )
        for id_ in ids:
            if id_ not in db_instances:
                raise ActionException(f"Id {id_} not in db_instances.")
            instance: dict[str, Any] = {
                "id": id_,
                "parent_id": parent_id,
                "owner_id": owner_id,
            }
            access_group_ids = list(db_instances[id_].get("access_group_ids", []))
            (
                instance["is_public"],
                instance["inherited_access_group_ids"],
            ) = calculate_inherited_groups_helper_with_parent_id(
                self.datastore,
                access_group_ids,
                instance.get("parent_id"),
            )
            yield instance

            # Handle children
            yield from self.handle_children(
                instance,
                instance["is_public"],
                instance["inherited_access_group_ids"],
            )
