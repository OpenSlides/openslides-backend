from typing import Any

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from ....shared.exceptions import ActionException
from ...action import Action


class ChatEnabledMixin(Action):
    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["enable_chat"],
            lock_result=False,
        )

        if not organization.get("enable_chat"):
            raise ActionException("Chat is not enabled.")
        return instance
