from typing import Any, Dict, List

import fastjsonschema

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportStatus, JsonUploadMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import UserCreate
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
        rows = [self.validate_entry(entry) for entry in data]

        self.init_rows(rows)
        self.store_rows_in_the_action_worker("account")
        return {}

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        status, error = None, []
        try:
            UserCreate.schema_validator(entry)
            if entry.get("username"):
                if self.check_username_for_duplicate(entry["username"]):
                    status = ImportStatus.UPDATE
                else:
                    status = ImportStatus.CREATE

            else:
                if not entry.get("first_name") and not entry.get("last_name"):
                    status = ImportStatus.ERROR
                    error.append("Cannot generate username.")
                elif self.check_name_and_email_for_duplicate(
                    entry.get("first_name"), entry.get("last_name"), entry.get("email")
                ):
                    status = ImportStatus.UPDATE
                else:
                    status = ImportStatus.CREATE
        except fastjsonschema.JsonSchemaException as exception:
            status = ImportStatus.ERROR
            error.append(exception.message)
        return {"status": status, "error": error, "data": entry}
