from typing import Any, Dict

from ..base import Action


class DeduplicatePermissionsMixin(Action):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deduplicate permissions
        """
        instance = super().update_instance(instance)
        if "permissions" in instance:
            instance["permissions"] = list(set(instance["permissions"]))
        return instance
