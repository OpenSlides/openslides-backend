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
            mediafile = self.database.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["parent_id"]
            )
            if mediafile.get("parent_id"):
                parent = self.database.get(
                    FullQualifiedId(self.model.collection, mediafile["parent_id"]),
                    ["has_inherited_access_groups", "inherited_access_group_ids"],
                )

                (
                    instance["has_inherited_access_groups"],
                    instance["inherited_access_group_ids"],
                ) = self.calculate_inherited_groups(
                    instance["id"],
                    instance["access_group_ids"],
                    parent.get("has_inherited_access_groups"),
                    parent.get("inherited_access_group_ids"),
                )
                yield instance

                # Handle children
                yield from self.handle_children(
                    instance,
                    instance["has_inherited_access_groups"],
                    instance["inherited_access_group_ids"],
                )
            else:
                instance["inherited_access_group_ids"] = instance["access_group_ids"]
                instance["has_inherited_access_groups"] = bool(
                    instance["inherited_access_group_ids"]
                )
                yield instance

    def handle_children(
        self,
        instance: Dict[str, Any],
        parent_has_inherited_access_groups: Optional[bool],
        parent_inherited_access_group_ids: Optional[List[int]],
    ) -> ActionPayload:
        mediafile = self.database.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["child_ids"]
        )
        if mediafile.get("child_ids"):
            for child_id in mediafile["child_ids"]:
                child = self.database.get(
                    FullQualifiedId(self.model.collection, child_id),
                    [
                        "access_group_ids",
                        "child_ids",
                        "has_inherited_access_groups",
                        "inherited_access_group_ids",
                    ],
                )
                new_instance = {"id": child_id}
                (
                    new_instance["has_inherited_access_groups"],
                    new_instance["inherited_access_group_ids"],
                ) = self.calculate_inherited_groups(
                    child_id,
                    child.get("access_group_ids", []),
                    parent_has_inherited_access_groups,
                    parent_inherited_access_group_ids,
                )

                if (
                    child.get("has_inherited_access_groups")
                    != new_instance["has_inherited_access_groups"]
                    or child.get("inherited_access_group_ids")
                    != new_instance["inherited_access_group_ids"]
                ):
                    yield new_instance
                    yield from self.handle_children(
                        new_instance,
                        new_instance["has_inherited_access_groups"],
                        new_instance["inherited_access_group_ids"],
                    )
