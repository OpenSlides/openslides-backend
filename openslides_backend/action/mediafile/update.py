from typing import Any, Dict

from ...models.models import Mediafile
from ..default_schema import DefaultSchema
from ..generics import UpdateAction
from ..register import register_action
from .calculate_mixins import MediafileCalculatedFieldsMixin


@register_action("mediafile.update")
class MediafileUpdate(MediafileCalculatedFieldsMixin, UpdateAction):
    """
    Action to update a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_update_schema(
        optional_properties=["title", "access_group_ids"]
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate inherited_access_group_ids and inherited_access_group_ids, if
        access_group_ids are given.
        """
        if instance.get("access_group_ids") is None:
            return instance
        (
            instance["has_inherited_access_groups"],
            instance["inherited_access_group_ids"],
        ) = self.calculate_inherited_groups(
            instance["id"], instance["access_group_ids"]
        )

        return instance
