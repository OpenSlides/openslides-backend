from typing import Any

from openslides_backend.shared.exceptions import ActionException 
from ...mixins.check_unique_name_mixin import CheckUniqueInContextMixin

class GenderUniqueMixin(CheckUniqueInContextMixin):
    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        self.check_unique_in_context(
            "name",
            instance["name"],
            "Gender '" + instance.get("name") + "' already exists.",
            instance.get("id"),
        )
    
class GenderPermissionMixin():
    def check_editable(self, instance: dict[str, Any]) -> None:
        if 0 < instance["id"] < 5:
            #if "name" in instance:
            #    gender = instance["name"] oder self.datastore.get(fqid_from_collection_and_id("gender", instance["id"]), ["name"])
           # else: 
           #     gender = instance["id"]
            gender = instance["id"]
            msg = f"Cannot delete or update gender '{gender}' from default selection."
            raise ActionException(msg)