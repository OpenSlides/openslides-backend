from typing import Any, Dict, List, Optional

from ...models.models import Mediafile
from ...services.datastore.commands import GetManyRequest
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId
from ...shared.schema import id_list_schema
from ..base import ActionPayload
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action
from .calculate_mixins import MediafileCalculatedFieldsMixin


@register_action("mediafile.move")
class MediafileMoveAction(UpdateAction, MediafileCalculatedFieldsMixin):
    """
    Action to move mediafiles.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_default_schema(
        title="Mediafile new parent schema",
        description="An object containing an array of mediafile ids and the new parent id the items should be moved to.",
        required_properties=["parent_id", "meeting_id"],
        additional_required_fields={
            "ids": {
                "description": "An array of agenda item ids where the items should be assigned to the new parent id.",
                **id_list_schema,
            }
        },
        single_item=True,
    )

    def check_is_directory(self, id_: int) -> None:
        item = self.datastore.get(
            FullQualifiedId(self.model.collection, id_), ["is_directory"]
        )
        if not item.get("is_directory"):
            raise ActionException("New parent is not a directory.")

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        yield from self.prepare_move_data(
            parent_id=instance["parent_id"],
            ids=instance["ids"],
            meeting_id=instance["meeting_id"],
        )

    def prepare_move_data(
        self, parent_id: Optional[int], ids: List[int], meeting_id: int
    ) -> ActionPayload:
        get_many_request = GetManyRequest(
            self.model.collection, ids, ["meeting_id", "access_group_ids"]
        )
        gm_result = self.datastore.get_many([get_many_request])
        db_instances = gm_result.get(self.model.collection, {})

        if parent_id is not None:
            self.check_is_directory(parent_id)

            # Calculate the ancesters of parent
            ancesters = [parent_id]
            grandparent = self.datastore.get(
                FullQualifiedId(self.model.collection, parent_id), ["parent_id"]
            )
            while grandparent.get("parent_id") is not None:
                gp_parent_id = grandparent["parent_id"]
                ancesters.append(gp_parent_id)
                grandparent = self.datastore.get(
                    FullQualifiedId(self.model.collection, gp_parent_id), ["parent_id"]
                )
            for id_ in ids:
                if id_ in ancesters:
                    raise ActionException(
                        f"Moving item {id_} to one of its children is not possible."
                    )
        for id_ in ids:
            if (
                id_ not in db_instances
                or db_instances[id_].get("meeting_id") != meeting_id
            ):
                raise ActionException(f"Id {id_} not in db_instances.")

            instance: Dict[str, Any] = {"id": id_, "parent_id": parent_id}
            access_group_ids = list(db_instances[id_].get("access_group_ids", []))
            if parent_id:
                parent = self.datastore.get(
                    FullQualifiedId(self.model.collection, parent_id),
                    ["is_public", "inherited_access_group_ids"],
                )

                (
                    instance["is_public"],
                    instance["inherited_access_group_ids"],
                ) = self.calculate_inherited_groups(
                    access_group_ids,
                    parent.get("is_public"),
                    parent.get("inherited_access_group_ids"),
                )
            else:
                instance["inherited_access_group_ids"] = access_group_ids
                instance["is_public"] = not bool(instance["inherited_access_group_ids"])

            yield instance

            # Handle children
            yield from self.handle_children(
                instance,
                instance["is_public"],
                instance["inherited_access_group_ids"],
            )
