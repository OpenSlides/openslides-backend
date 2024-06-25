from typing import Any

from openslides_backend.shared.exceptions import ActionException 
from ...mixins.check_unique_name_mixin import CheckUniqueInContextMixin
from datastore.shared.util import fqid_from_collection_and_id

class GenderUniqueMixin(CheckUniqueInContextMixin):
    def validate_instance(self, instance: dict[str, Any]) -> None:
        super().validate_instance(instance)
        if instance.get("name") == "":
            raise ActionException("Empty gender name not allowed.")
        self.check_unique_in_context(
            "name",
            instance["name"],
            "Gender '" + instance.get("name") + "' already exists.",
            instance.get("id"),
        )
    
class GenderPermissionMixin():
    def check_editable(self, instance: dict[str, Any]) -> None:
        gender = instance.get("id")
        if 0 < gender < 5:
            if gender_name := self.datastore.get(fqid_from_collection_and_id("gender", instance["id"]), ["name"]).get("name"):
                gender = gender_name
            #if "name" in instance:
            #    gender = instance["name"] oder self.datastore.get(fqid_from_collection_and_id("gender", instance["id"]), ["name"])
           # else: 
           #     gender = instance["id"]
            msg = f"Cannot delete or update gender '{gender}' from default selection."
            raise ActionException(msg)