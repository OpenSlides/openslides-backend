from typing import Any

from ...shared.exceptions import ActionException
from ...shared.patterns import fqid_from_collection_and_id
from ..action import Action


class ForbidAnonymousGroupMixin(Action):
    def check_anonymous_not_in_list_fields(
        self,
        instance: dict[str, Any],
        group_list_field_names: list[str],
        anonymous_group_id: int | None = None,
    ) -> None:
        if not anonymous_group_id:
            anonymous_group_id = self.datastore.get(
                fqid_from_collection_and_id("meeting", self.get_meeting_id(instance)),
                ["anonymous_group_id"],
            ).get("anonymous_group_id")
        if anonymous_group_id:
            for field in group_list_field_names:
                if anonymous_group_id in instance.get(field, []):
                    raise ActionException(f"Anonymous group is not allowed in {field}.")
