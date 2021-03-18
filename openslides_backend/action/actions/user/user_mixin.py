from typing import Any, Dict

from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection
from ...action import Action


class UserMixin(Action):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if "username" in instance:
            exists = self.datastore.exists(
                Collection("user"),
                FilterOperator("username", "=", instance["username"]),
                lock_result=True,
            )
            if exists:
                raise ActionException(
                    f"A user with the username {instance['username']} already exists."
                )
        return instance
