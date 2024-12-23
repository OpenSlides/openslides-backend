import time
from typing import Any

import time
from typing import Any

import fastjsonschema

from openslides_backend.permissions.permissions import Permissions
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.register import register_action
from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.schema import schema_version

@register_action("user.backchannel_login")
class UserBackchannelLogin(
    SingularActionMixin,
):
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
                "idp_id": {"type": "string"}
            },
            "required": ["idp_id"],
            "additionalProperties": False
        }

    permission = Permissions.System.CAN_LOGIN
    history_information = "User back-channel login"

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        idp_id = instance.get("idp_id")
        user = self.datastore.get(
            self.model.collection,
            self.model.default_values,
            {"idp_id": idp_id},
        )
        if not user:
            raise ActionException(f"User with idp_id {idp_id} not found.")
        instance["last_login"] = int(time.time())
        return instance
