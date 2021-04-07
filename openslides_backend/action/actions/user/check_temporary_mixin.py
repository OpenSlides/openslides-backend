from typing import Any, Dict

from openslides_backend.permissions.permission_helper import is_temporary

from ....shared.exceptions import ActionException
from ...action import BaseAction


class CheckTemporaryMixin(BaseAction):
    """
    Mixin to provide check_for_temporary().
    """

    def check_for_temporary(self, instance: Dict[str, Any]) -> None:
        if not is_temporary(self.datastore, instance):
            raise ActionException(f"User {instance['id']} is not temporary.")

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        super().validate_instance(instance)  # type: ignore
        self.check_for_temporary(instance)
