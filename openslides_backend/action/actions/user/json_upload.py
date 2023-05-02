from typing import Any, Dict, Tuple

import fastjsonschema

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportStatus, JsonUploadMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import UserCreate
from .password_mixin import PasswordCreateMixin
from .user_mixin import DuplicateCheckMixin, UsernameMixin


@register_action("user.json_upload")
class UserJsonUpload(DuplicateCheckMixin, UsernameMixin, JsonUploadMixin):
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
        self.init_duplicate_set(
            [
                {
                    field: entry.get(field, "")
                    for field in ("username", "first_name", "last_name", "email")
                }
                for entry in data
            ]
        )
        rows = [
            self.generate_entry(entry, payload_index)
            for payload_index, entry in enumerate(data)
        ]

        self.init_rows(rows)
        self.store_rows_in_the_action_worker("account")
        return {}

    def generate_entry(
        self, entry: Dict[str, Any], payload_index: int
    ) -> Dict[str, Any]:
        status, error = None, []
        try:
            UserCreate.schema_validator(entry)
            if entry.get("username"):
                if self.check_username_for_duplicate(entry["username"], payload_index):
                    status = ImportStatus.DONE
                    if searchdata := self.get_search_data(payload_index):
                        entry["id"] = searchdata["id"]
                    else:
                        status = ImportStatus.ERROR
                        error.append(f"Duplicate in csv list index: {payload_index}")
                else:
                    status = ImportStatus.NEW
                entry["username"] = {"value": entry["username"], "info": "done"}
            else:
                if not (entry.get("first_name") or entry.get("last_name")):
                    status = ImportStatus.ERROR
                    error.append("Cannot generate username.")
                elif self.check_name_and_email_for_duplicate(
                    *self._names_and_email(entry), payload_index
                ):
                    status = ImportStatus.DONE
                    if searchdata := self.get_search_data(payload_index):
                        entry["username"] = {
                            "value": searchdata["username"],
                            "info": ImportStatus.DONE,
                        }
                        entry["id"] = searchdata["id"]
                    else:
                        status = ImportStatus.ERROR
                        error.append("Duplicate in csv list index: {payload_index}")
                else:
                    status = ImportStatus.NEW
                    entry["username"] = {
                        "value": self.generate_username(entry),
                        "info": ImportStatus.GENERATED,
                    }
            self.handle_default_password(entry, status)
        except fastjsonschema.JsonSchemaException as exception:
            status = ImportStatus.ERROR
            error.append(exception.message)
        return {"status": status, "error": error, "data": entry}

    def handle_default_password(self, entry: Dict[str, Any], status: str) -> None:
        if status == ImportStatus.NEW:
            if "default_password" in entry:
                value = entry["default_password"]
                info = ImportStatus.DONE
            else:
                value = PasswordCreateMixin.generate_password()
                info = ImportStatus.GENERATED
            entry["default_password"] = {"value": value, "info": info}
        elif status in (ImportStatus.DONE, ImportStatus.ERROR):
            if "default_password" in entry:
                entry["default_password"] = {
                    "value": entry["default_password"],
                    "info": ImportStatus.DONE,
                }

    def _names_and_email(self, entry: Dict[str, Any]) -> Tuple[str, str, str]:
        return (
            entry.get("first_name", ""),
            entry.get("last_name", ""),
            entry.get("email", ""),
        )
