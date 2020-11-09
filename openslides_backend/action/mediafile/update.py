from typing import Any, Dict, List, Optional

from ...models.models import Mediafile
from ...shared.patterns import FullQualifiedId
from ..action_interface import ActionPayload
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action
from .calculate_mixins import MediafileCalculatedFieldsMixin


@register_action("mediafile.update")
class MediafileUpdate(UpdateAction, MediafileCalculatedFieldsMixin):
    """
    Action to update a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_update_schema(
        optional_properties=["title", "access_group_ids"]
    )

    def get_updated_instances(self, instances: ActionPayload) -> ActionPayload:
        """
        Calculate inherited_access_group_ids and inherited_access_group_ids, if
        access_group_ids are given.
        """
        for instance in instances:
            if instance.get("access_group_ids") is None:
                yield instance
                continue
            mediafile = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["parent_id"]
            )
            if mediafile.get("parent_id"):
                parent = self.datastore.get(
                    FullQualifiedId(self.model.collection, mediafile["parent_id"]),
                    ["is_public", "inherited_access_group_ids"],
                )

                (
                    instance["is_public"],
                    instance["inherited_access_group_ids"],
                ) = self.calculate_inherited_groups(
                    instance["access_group_ids"],
                    parent.get("is_public"),
                    parent.get("inherited_access_group_ids"),
                )
                yield instance

                # Handle children
                yield from self.handle_children(
                    instance,
                    instance["is_public"],
                    instance["inherited_access_group_ids"],
                )
            else:
                instance["inherited_access_group_ids"] = instance["access_group_ids"]
                instance["is_public"] = not bool(instance["inherited_access_group_ids"])
                yield instance

    def handle_children(
        self,
        instance: Dict[str, Any],
        parent_is_public: Optional[bool],
        parent_inherited_access_group_ids: Optional[List[int]],
    ) -> ActionPayload:
        mediafile = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["child_ids"]
        )
        if mediafile.get("child_ids"):
            for child_id in mediafile["child_ids"]:
                child = self.datastore.get(
                    FullQualifiedId(self.model.collection, child_id),
                    [
                        "access_group_ids",
                        "child_ids",
                        "is_public",
                        "inherited_access_group_ids",
                    ],
                )
                new_instance = {"id": child_id}
                (
                    new_instance["is_public"],
                    new_instance["inherited_access_group_ids"],
                ) = self.calculate_inherited_groups(
                    child.get("access_group_ids", []),
                    parent_is_public,
                    parent_inherited_access_group_ids,
                )

                if (
                    child.get("is_public") != new_instance["is_public"]
                    or child.get("inherited_access_group_ids")
                    != new_instance["inherited_access_group_ids"]
                ):
                    yield new_instance
                    yield from self.handle_children(
                        new_instance,
                        new_instance["is_public"],
                        new_instance["inherited_access_group_ids"],
                    )
