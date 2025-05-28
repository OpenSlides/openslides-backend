from typing import Any

from ....models.models import ListOfSpeakers
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import MissingPermission
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("list_of_speakers.update")
class ListOfSpeakersUpdateAction(UpdateAction):
    """
    Action to update a list of speakers.
    """

    model = ListOfSpeakers()
    schema = DefaultSchema(ListOfSpeakers()).get_update_schema(
        optional_properties=["closed", "moderator_notes"]
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if "moderator_notes" in instance:
            perm = Permissions.ListOfSpeakers.CAN_MANAGE_MODERATOR_NOTES
            if not has_perm(
                self.datastore,
                self.user_id,
                perm,
                self.get_meeting_id(instance),
            ):
                raise MissingPermission(perm)
            if len(instance) == 2:
                return
        super().check_permissions(instance)
