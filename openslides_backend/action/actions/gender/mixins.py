from typing import Any

from datastore.shared.util import fqid_from_collection_and_id

from openslides_backend.action.action import Action
from openslides_backend.shared.exceptions import ActionException, PermissionException

from ...mixins.check_unique_name_mixin import CheckUniqueInContextMixin


class GenderUniqueMixin(CheckUniqueInContextMixin):
    def validate_instance(self, instance: dict[str, Any]) -> None:
        if instance.get("name") == "":
            raise ActionException("Empty gender name not allowed.")
        super().validate_instance(instance)
        self.check_unique_in_context(
            "name",
            instance.get("name", ""),
            "Gender '" + instance.get("name", "") + "' already exists.",
            instance.get("id"),
        )


class GenderPermissionMixin(Action):
    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)
        # default genders shall not be mutable
        gender_id = instance.get("id", 0)
        if 0 < gender_id < 5:
            if gender_name := self.datastore.get(
                fqid_from_collection_and_id("gender", gender_id),
                ["name"],
                lock_result=False,
            ).get("name"):
                msg = f"Cannot delete or update gender '{gender_name}' from default selection."
            else:
                msg = f"Cannot delete or update gender '{gender_id}' from default selection."
            raise PermissionException(msg)
