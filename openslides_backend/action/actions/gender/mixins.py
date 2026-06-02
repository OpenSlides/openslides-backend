from typing import Any

from openslides_backend.action.action import Action
from openslides_backend.shared.exceptions import PermissionException
from openslides_backend.shared.patterns import fqid_from_collection_and_id


class GenderPermissionMixin(Action):
    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)
        # default genders shall not be mutable
        gender_id = instance.get("id", 0)
        if 0 < gender_id < 5:
            gender_name = self.datastore.get(
                fqid_from_collection_and_id("gender", gender_id),
                ["name"],
                lock_result=False,
            ).get("name")
            msg = f"Cannot delete or update gender '{gender_name}' from default selection."
            raise PermissionException(msg)
