from typing import Any, Dict, Tuple

import fastjsonschema

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportState, JsonUploadMixin
from ...util.crypto import get_random_password
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import UserCreate
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
        self.rows = [
            self.generate_entry(entry, payload_index)
            for payload_index, entry in enumerate(data)
        ]

        # generate statistics
        itemCount = len(self.rows)
        state_to_count = {state: 0 for state in ImportState}
        for entry in self.rows:
            state_to_count[entry["state"]] += 1

        self.statistics = [
            {"name": "total", "value": itemCount},
            {"name": "created", "value": state_to_count[ImportState.NEW]},
            {"name": "updated", "value": state_to_count[ImportState.DONE]},
            {"name": "error", "value": state_to_count[ImportState.ERROR]},
            {"name": "warning", "value": state_to_count[ImportState.WARNING]},
        ]

        self.set_state(
            state_to_count[ImportState.ERROR], state_to_count[ImportState.WARNING]
        )
        self.store_rows_in_the_action_worker("account")
        return {}

    def generate_entry(
        self, entry: Dict[str, Any], payload_index: int
    ) -> Dict[str, Any]:
        state, messages = None, []
        try:
            UserCreate.schema_validator(entry)
            if entry.get("username"):
                if self.check_username_for_duplicate(entry["username"], payload_index):
                    state = ImportState.DONE
                    if searchdata := self.get_search_data(payload_index):
                        entry["username"] = {
                            "value": entry["username"],
                            "info": "done",
                            "id": searchdata["id"],
                        }
                    else:
                        entry["username"] = {"value": entry["username"], "info": "done"}
                        state = ImportState.ERROR
                        messages.append(f"Duplicate in csv list index: {payload_index}")
                else:
                    state = ImportState.NEW
                    entry["username"] = {"value": entry["username"], "info": "done"}
            else:
                if not (entry.get("first_name") or entry.get("last_name")):
                    state = ImportState.ERROR
                    messages.append("Cannot generate username.")
                elif self.check_name_and_email_for_duplicate(
                    *UserJsonUpload._names_and_email(entry), payload_index
                ):
                    state = ImportState.DONE
                    if searchdata := self.get_search_data(payload_index):
                        entry["username"] = {
                            "value": searchdata["username"],
                            "info": ImportState.DONE,
                            "id": searchdata["id"],
                        }
                    else:
                        state = ImportState.ERROR
                        if usernames := self.has_multiple_search_data(payload_index):
                            messages.append(
                                "Found more than one user: " + ", ".join(usernames)
                            )
                        else:
                            messages.append(
                                f"Duplicate in csv list index: {payload_index}"
                            )
                else:
                    state = ImportState.NEW
                    entry["username"] = {
                        "value": self.generate_username(entry),
                        "info": ImportState.GENERATED,
                    }
            self.handle_default_password(entry, state)
        except fastjsonschema.JsonSchemaException as exception:
            state = ImportState.ERROR
            messages.append(exception.message)
        return {"state": state, "messages": messages, "data": entry}

    def handle_default_password(self, entry: Dict[str, Any], state: str) -> None:
        if state == ImportState.NEW:
            if "default_password" in entry:
                value = entry["default_password"]
                info = ImportState.DONE
            else:
                value = get_random_password()
                info = ImportState.GENERATED
            entry["default_password"] = {"value": value, "info": info}
        elif state in (ImportState.DONE, ImportState.ERROR):
            if "default_password" in entry:
                entry["default_password"] = {
                    "value": entry["default_password"],
                    "info": ImportState.DONE,
                }

    @staticmethod
    def _names_and_email(entry: Dict[str, Any]) -> Tuple[str, str, str]:
        return (
            entry.get("first_name", ""),
            entry.get("last_name", ""),
            entry.get("email", ""),
        )
