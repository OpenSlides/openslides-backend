from ....models.models import Mediafile
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
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

    def get_updated_instances(self, instances: ActionData) -> ActionData:
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
            else:
                instance["inherited_access_group_ids"] = instance["access_group_ids"]
                instance["is_public"] = not bool(instance["inherited_access_group_ids"])

            yield instance

            # Handle children
            yield from self.handle_children(
                instance,
                instance["is_public"],
                instance["inherited_access_group_ids"],
            )
