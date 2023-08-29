from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ...mixins.import_mixins import ImportState, JsonUploadMixin, Lookup, ResultType
from ...util.crypto import get_random_password
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .user_mixin import UsernameMixin


@register_action("account.json_upload")
class AccountJsonUpload(JsonUploadMixin, UsernameMixin):
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
                            "saml_id",
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
        {"property": "default_password", "type": "string", "is_object": True},
        {"property": "email", "type": "string"},
        {"property": "username", "type": "string", "is_object": True},
        {"property": "gender", "type": "string"},
        {"property": "pronoun", "type": "string"},
        {"property": "saml_id", "type": "string", "is_object": True},
    ]
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    skip_archived_meeting_check = True
    row_state: ImportState
    username_lookup: Lookup
    saml_id_lookup: Lookup
    names_email_lookup: Lookup
    all_saml_id_lookup: Lookup

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")
        data = self.add_payload_index_to_action_data(data)
        self.setup_lookups(data)

        self.rows = [
            self.validate_entry(entry, payload_index)
            for payload_index, entry in enumerate(data)
        ]

        # generate statistics
        itemCount = len(self.rows)
        state_to_count = {state: 0 for state in ImportState}
        for entry in self.rows:
            state_to_count[entry["state"]] += 1
            entry["data"].pop("payload_index", None)

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

    def validate_entry(
        self, entry: Dict[str, Any], payload_index: int
    ) -> Dict[str, Any]:
        messages: List[str] = []
        id_: Optional[int] = None
        if username := entry.get("username"):
            check_result = self.username_lookup.check_duplicate(username)
            id_ = self.username_lookup.get_x_by_name(username, "id")
            if check_result == ResultType.FOUND_ID and id_ != 0:
                self.row_state = ImportState.DONE
                entry["id"] = id_
                entry["username"] = {
                    "value": username,
                    "info": ImportState.DONE,
                    "id": id_,
                }
            elif check_result == ResultType.NOT_FOUND or id_ == 0:
                self.row_state = ImportState.NEW
                entry["username"] = {
                    "value": username,
                    "info": ImportState.DONE,
                }
            elif check_result == ResultType.FOUND_MORE_IDS:
                self.row_state = ImportState.ERROR
                entry["username"] = {
                    "value": username,
                    "info": ImportState.ERROR,
                }
                messages.append("Found more users with the same username")
        elif saml_id := entry.get("saml_id"):
            check_result = self.saml_id_lookup.check_duplicate(saml_id)
            id_ = self.saml_id_lookup.get_x_by_name(saml_id, "id")
            username = self.saml_id_lookup.get_x_by_name(saml_id, "username")
            if check_result == ResultType.FOUND_ID and id_ != 0:
                self.row_state = ImportState.DONE
                entry["id"] = id_
                entry["username"] = {
                    "value": username,
                    "info": ImportState.DONE,
                    "id": id_,
                }
            elif check_result == ResultType.NOT_FOUND or id_ == 0:
                self.row_state = ImportState.NEW
            elif check_result == ResultType.FOUND_MORE_IDS:
                self.row_state = ImportState.ERROR
                messages.append("Found more users with the same saml_id")
        else:
            if not (entry.get("first_name") or entry.get("last_name")):
                self.row_state = ImportState.ERROR
                messages.append("Cannot generate username.")
            else:
                names_and_email = self._names_and_email(entry)
                check_result = self.names_email_lookup.check_duplicate(names_and_email)
                id_ = self.names_email_lookup.get_x_by_name(names_and_email, "id")
                username = self.names_email_lookup.get_x_by_name(
                    names_and_email, "username"
                )
                if check_result == ResultType.FOUND_ID and id_ != 0:
                    self.row_state = ImportState.DONE
                    entry["id"] = id_
                    entry["username"] = {
                        "value": username,
                        "info": ImportState.DONE,
                        "id": id_,
                    }
                elif check_result == ResultType.NOT_FOUND or id_ == 0:
                    self.row_state = ImportState.NEW
                elif check_result == ResultType.FOUND_MORE_IDS:
                    self.row_state = ImportState.ERROR
                    messages.append("Found more users with name and email")

        if id_ and len(self.all_id_mapping.get(id_, [])) > 1:
            self.row_state = ImportState.ERROR
            messages.append(
                f"The account with id {id_} was found multiple times by different search criteria."
            )

        if not entry.get("username") and self.row_state == ImportState.NEW:
            entry["username"] = {
                "value": self.generate_username(entry) or entry.get("saml_id"),
                "info": ImportState.GENERATED,
            }

        self.handle_default_password(entry)
        if saml_id := entry.get("saml_id"):
            check_result = self.all_saml_id_lookup.check_duplicate(saml_id)
            if id_ := entry.get("id"):
                if check_result == ResultType.FOUND_ID:
                    idFound = self.all_saml_id_lookup.get_x_by_name(saml_id, "id")
                if check_result == ResultType.NOT_FOUND or (
                    check_result == ResultType.FOUND_ID and id_ == idFound
                ):
                    entry["saml_id"] = {
                        "value": saml_id,
                        "info": ImportState.DONE,
                    }
                else:
                    self.row_state = ImportState.ERROR
                    messages.append(f"saml_id {saml_id} must be unique.")
                    entry["saml_id"] = {
                        "value": saml_id,
                        "info": ImportState.ERROR,
                    }
            else:
                if check_result != ResultType.NOT_FOUND:
                    self.row_state = ImportState.ERROR
                    entry["saml_id"] = {
                        "value": saml_id,
                        "info": ImportState.ERROR,
                    }
                    messages.append(f"saml_id {saml_id} must be unique.")
                else:
                    entry["saml_id"] = {
                        "value": saml_id,
                        "info": ImportState.NEW,
                    }

            if entry.get("password") or entry.get("default_password"):
                messages.append("Removed password or default_password from entry.")
                entry.pop("password", None)
                entry.pop("default_password", None)
                entry["can_change_own_password"] = False
        return {"state": self.row_state, "messages": messages, "data": entry}

    def handle_default_password(self, entry: Dict[str, Any]) -> None:
        if self.row_state == ImportState.NEW:
            if "default_password" in entry:
                value = entry["default_password"]
                info = ImportState.DONE
            else:
                value = get_random_password()
                info = ImportState.GENERATED
            entry["default_password"] = {"value": value, "info": info}
        elif self.row_state in (ImportState.DONE, ImportState.ERROR):
            if "default_password" in entry:
                entry["default_password"] = {
                    "value": entry["default_password"],
                    "info": ImportState.DONE,
                }

    @staticmethod
    def _names_and_email(entry: Dict[str, Any]) -> Tuple[str, ...]:
        return (
            entry.get("first_name", ""),
            entry.get("last_name", ""),
            entry.get("email", ""),
        )

    def setup_lookups(self, data: List[Dict[str, Any]]) -> None:
        self.username_lookup = Lookup(
            self.datastore,
            "user",
            [
                (username, entry)
                for entry in data
                if (username := entry.get("username"))
            ],
            field="username",
        )
        self.saml_id_lookup = Lookup(
            self.datastore,
            "user",
            [
                (saml_id, entry)
                for entry in data
                if not entry.get("username") and (saml_id := entry.get("saml_id"))
            ],
            field="saml_id",
            mapped_fields=["username"],
        )
        self.names_email_lookup = Lookup(
            self.datastore,
            "user",
            [
                (names_email, entry)
                for entry in data
                if not entry.get("username")
                and not entry.get("saml_id")
                and (
                    names_email := (
                        entry.get("first_name", ""),
                        entry.get("last_name", ""),
                        entry.get("email", ""),
                    )
                )
            ],
            field=tuple(("first_name", "last_name", "email")),
            mapped_fields=["username"],
        )
        self.all_saml_id_lookup = Lookup(
            self.datastore,
            "user",
            [(saml_id, entry) for entry in data if (saml_id := entry.get("saml_id"))],
            field="saml_id",
            mapped_fields=["username"],
        )

        self.all_id_mapping: Dict[int, List[Union[str, Tuple[str, ...]]]] = defaultdict(
            list
        )
        for id, values in self.username_lookup.id_to_name.items():
            self.all_id_mapping[id].extend(values)
        for id, values in self.saml_id_lookup.id_to_name.items():
            self.all_id_mapping[id].extend(values)
        for id, values in self.names_email_lookup.id_to_name.items():
            self.all_id_mapping[id].extend(values)
