from typing import Any

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportState
from ...util.register import register_action
from .base_json_upload import BaseUserJsonUpload


@register_action("account.json_upload")
class AccountJsonUpload(BaseUserJsonUpload):
    """
    Action to allow to upload a json. It is used as first step of an import.
    """

    schema = BaseUserJsonUpload.get_schema(
        additional_user_fields=User().get_properties(
            "default_vote_weight",
        ),
    )
    headers = BaseUserJsonUpload.headers + [
        {"property": "default_vote_weight", "type": "decimal", "is_object": True},
    ]
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    import_name = "account"

    def validate_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        results = super().validate_entry(entry)

        messages = results["messages"]

        if vote_weight := (entry := results["data"]).get("default_vote_weight"):
            if vote_weight == "0.000000":
                entry["default_vote_weight"] = {
                    "value": vote_weight,
                    "info": ImportState.ERROR,
                }
                messages.append(
                    "default_vote_weight must be bigger than or equal to 0.000001."
                )
                results["state"] = ImportState.ERROR
            else:
                entry["default_vote_weight"] = {
                    "value": vote_weight,
                    "info": ImportState.DONE,
                }

        if self.user_id == entry.get("id") and not (
            is_active := entry.get("is_active", True)
        ):
            entry["is_active"] = {
                "value": is_active,
                "info": ImportState.ERROR,
            }
            messages.append("A superadmin is not allowed to set himself inactive.")

        self.check_field_failures(
            entry,
            messages,
            "Account is updated, but changes to the following field(s) are not possible:",
            field_groups="ADEFGHIJ",
        )

        return results
