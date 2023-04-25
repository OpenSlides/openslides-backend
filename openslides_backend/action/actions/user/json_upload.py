import re
from typing import Any, Dict, List, Tuple

import fastjsonschema

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportStatus, JsonUploadMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import UserCreate
from .password_mixin import PasswordCreateMixin
from .user_mixin import DuplicateCheckMixin


@register_action("user.json_upload")
class UserJsonUpload(DuplicateCheckMixin, JsonUploadMixin):
    """
    Action to allow to upload a json. It is used as first step of an import.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        additional_required_fields={
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        **model.get_properties(
                            "title",
                            "first_name",
                            "last_name",
                            "is_active",
                            "is_physical_person",
                            "default_password",
                            "email",
                            "username",
                            "gender",
                            "pronoun",
                        ),
                    },
                    "required": [],
                    "additionalProperties": False,
                },
                "minItems": 1,
                "uniqueItems": False,
            },
        }
    )
    headers = [
        {"property": "title", "type": "string"},
        {"property": "first_name", "type": "string"},
        {"property": "last_name", "type": "string"},
        {"property": "is_active", "type": "boolean"},
        {"property": "is_physical_person", "type": "boolean"},
        {"property": "default_password", "type": "string"},
        {"property": "email", "type": "string"},
        {"property": "username", "type": "string"},
        {"property": "gender", "type": "string"},
        {"property": "pronoun", "type": "string"},
    ]
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")

        # validate and check for duplicates
        usernames: List[str] = []
        names_and_emails: List[Any] = []
        for entry in data:
            if entry.get("username"):
                usernames.append(entry["username"])
            elif entry.get("first_name") or entry.get("last_name"):
                names_and_emails.append(
                    (
                        entry.get("first_name"),
                        entry.get("last_name"),
                        entry.get("email"),
                    )
                )
        self.init_duplicate_set(usernames, names_and_emails)
        rows = [self.generate_entry(entry) for entry in data]

        self.init_rows(rows)
        self.store_rows_in_the_action_worker("account")
        return {}

    def generate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        status, error = None, []
        try:
            UserCreate.schema_validator(entry)
            if entry.get("username"):
                if self.check_username_for_duplicate(entry["username"]):
                    status = ImportStatus.DONE
                    if self.username_to_id[entry["username"]]:
                        entry["id"] = self.username_to_id[entry["username"]]
                else:
                    status = ImportStatus.NEW
                entry["username"] = {"value": entry["username"], "info": "done"}
            else:
                if not (
                    entry.get("first_name")
                    and entry.get("last_name")
                    and entry.get("email")
                ):
                    status = ImportStatus.ERROR
                    error.append("Cannot generate username.")
                elif self.check_name_and_email_for_duplicate(*_names_and_email(entry)):
                    status = ImportStatus.DONE
                    entry["username"] = {"value": entry["username"], "info": "done"}
                    if self.names_and_email_to_id[_names_and_email(entry)]:
                        entry["id"] = self.names_and_email_to_id[
                            _names_and_email(entry)
                        ]
                else:
                    status = ImportStatus.NEW
                    entry["username"] = {
                        "value": self.generate_username(entry),
                        "info": "generated",
                    }
            self.handle_default_password(entry, status)
        except fastjsonschema.JsonSchemaException as exception:
            status = ImportStatus.ERROR
            error.append(exception.message)
        return {"status": status, "error": error, "data": entry}

    def generate_username(self, entry: Dict[str, Any]) -> str:
        return re.sub(
            r"\W",
            "",
            entry.get("first_name", "") + entry.get("last_name", ""),
        )

    def handle_default_password(self, entry: Dict[str, Any], status: str) -> None:
        if status == ImportStatus.NEW:
            if "default_password" in entry:
                value = entry["default_password"]
                info = "done"
            else:
                value = PasswordCreateMixin.generate_password()
                info = "generated"
            entry["default_password"] = {"value": value, "info": info}
        elif status == ImportStatus.DONE:
            if "default_password" in entry:
                entry["default_password"] = {
                    "value": entry["default_password"],
                    "info": "done",
                }


def _names_and_email(entry: Dict[str, Any]) -> Tuple[str, str, str]:
    return (entry["first_name"], entry["last_name"], entry["email"])
