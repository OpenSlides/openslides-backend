from typing import Any, Dict

from openslides_backend.permissions.permission_helper import is_temporary

from ....shared.exceptions import ActionException
from ...action import BaseAction


class CheckTemporaryYesForInstanceMixin(BaseAction):
    """
    Mixin to provide instance-check_for_temporary user
    """

    def check_for_temporary(self, instance: Dict[str, Any]) -> None:
        if not is_temporary(self.datastore, instance):
            raise ActionException(f"User {instance['id']} in payload is not temporary.")

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        super().validate_instance(instance)  # type: ignore
        self.check_for_temporary(instance)


class CheckTemporaryNoForInstanceMixin(BaseAction):
    """
    Mixin to provide instance-check_for_non_temporary().
    """

    def check_for_not_temporary(self, instance: Dict[str, Any]) -> None:
        if is_temporary(self.datastore, instance):
            raise ActionException(
                f"User {instance['id']} in payload may not be a temporary user."
            )

    def validate_instance(self, instance: Dict[str, Any]) -> None:
        super().validate_instance(instance)  # type: ignore
        self.check_for_not_temporary(instance)
