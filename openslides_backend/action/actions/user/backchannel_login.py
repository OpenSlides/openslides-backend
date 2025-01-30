import time
from typing import Any, Iterable

from datastore.shared.util import FilterOperator
from openslides_backend.permissions.permissions import Permissions
from ...action import Action
from ...util.register import register_action
from ...util.typing import ActionResultElement
from ....models.models import User
from ....permissions.management_levels import SystemManagementLevel
from ....shared.exceptions import ActionException
from ....shared.interfaces.event import Event
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import schema_version


@register_action("user.backchannel_login")
class UserBackchannelLogin(Action):
    """
    Action to login a user via back-channel.
    """

    model = User()
    # must contain an object with a string attribute "idp_id"
    schema = {
        "$schema": schema_version,
        "title": "User login hook schema",
        "type": "object",
        "properties": {
            "os_uid": {"type": "integer"}
        },
        "required": ["os_uid"],
        "additionalProperties": False
    }

    permission = SystemManagementLevel(Permissions.System.CAN_LOGIN)
    history_information = "User back-channel login"
    skip_archived_meeting_check = True

    def create_action_result_element(self, instance: dict[str, Any]) -> ActionResultElement | None:
        return instance

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        os_uid = instance.get("os_uid")
        user = self.datastore.get(fqid_from_collection_and_id(self.model.collection, os_uid), ["id"])
        if not user:
            raise ActionException(f"User with id {os_uid} not found.")
        instance["last_login"] = int(time.time())
        instance["id"] = user["id"]
        return instance

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        return []
