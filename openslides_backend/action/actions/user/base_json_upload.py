from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, cast

from ....models.models import User
from ....shared.exceptions import ActionException
from ...mixins.import_mixins import (
    BaseJsonUploadAction,
    ImportState,
    Lookup,
    ResultType,
    SearchFieldType,
)
from ...util.crypto import get_random_password
from ...util.default_schema import DefaultSchema
from .user_mixins import UsernameMixin, check_gender_helper


class BaseUserJsonUpload(UsernameMixin, BaseJsonUploadAction):
    model = User()
    headers = [
        {"property": "title", "type": "string"},
        {"property": "first_name", "type": "string"},
        {"property": "last_name", "type": "string"},
        {"property": "is_active", "type": "boolean"},
        {"property": "is_physical_person", "type": "boolean"},
        {"property": "default_password", "type": "string", "is_object": True},
        {"property": "email", "type": "string"},
        {"property": "username", "type": "string", "is_object": True},
        {"property": "gender", "type": "string", "is_object": True},
        {"property": "pronoun", "type": "string"},
        {"property": "saml_id", "type": "string", "is_object": True},
    ]
    skip_archived_meeting_check = True
    row_state: ImportState
    username_lookup: Lookup
    saml_id_lookup: Lookup
    names_email_lookup: Lookup
    all_saml_id_lookup: Lookup

    @classmethod
    def get_schema(
        cls,
        additional_user_fields: Dict[str, Any],
        additional_required_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return DefaultSchema(User()).get_default_schema(
            additional_required_fields={
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            **cls.model.get_properties(
                                "username",
                                "first_name",
                                "last_name",
                                "email",
                                "title",
                                "pronoun",
                                "gender",
                                "default_password",
                                "is_active",
                                "is_physical_person",
                                "saml_id",
                            ),
                            **additional_user_fields,
                        },
                        "additionalProperties": False,
                    },
                    "minItems": 1,
                },
                **(additional_required_fields or {}),
            }
        )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        data = instance.pop("data")
        data = self.add_payload_index_to_action_data(data)
        self.setup_lookups(data, instance.get("meeting_id"))
        self.distribute_found_value_to_data(data)
        self.create_usernames(data)

        self.rows = [self.validate_entry(entry) for entry in data]
        self.generate_statistics()
        return {}

    def validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        messages: List[str] = []
        id_: Optional[int] = None
        old_saml_id: Optional[str] = None
        old_default_password: Optional[str] = None
        if (username := entry.get("username")) and isinstance(username, str):
            check_result = self.username_lookup.check_duplicate(username)
            id_ = cast(int, self.username_lookup.get_field_by_name(username, "id"))
            if check_result == ResultType.FOUND_ID and id_ != 0:
                old_saml_id = cast(
                    str, self.username_lookup.get_field_by_name(username, "saml_id")
                )
                old_default_password = cast(
                    str,
                    self.username_lookup.get_field_by_name(
                        username, "default_password"
                    ),
                )
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
            id_ = cast(int, self.saml_id_lookup.get_field_by_name(saml_id, "id"))
            if check_result == ResultType.FOUND_ID and id_ != 0:
                username = self.saml_id_lookup.get_field_by_name(saml_id, "username")
                old_saml_id = cast(
                    str, self.saml_id_lookup.get_field_by_name(saml_id, "saml_id")
                )
                old_default_password = cast(
                    str,
                    self.saml_id_lookup.get_field_by_name(saml_id, "default_password"),
                )

                self.row_state = ImportState.DONE
                entry["id"] = id_
                entry["username"] = {
                    "value": username,
                    "info": ImportState.DONE,
                    "id": id_,
                }
            elif check_result == ResultType.NOT_FOUND or id_ == 0:
                self.row_state = ImportState.NEW
        else:
            if not (entry.get("first_name") or entry.get("last_name")):
                self.row_state = ImportState.ERROR
                messages.append(
                    "Cannot generate username. Missing one of first_name, last_name."
                )
            else:
                names_and_email = self._names_and_email(entry)
                check_result = self.names_email_lookup.check_duplicate(names_and_email)
                id_ = cast(
                    int,
                    self.names_email_lookup.get_field_by_name(names_and_email, "id"),
                )
                if check_result == ResultType.FOUND_ID and id_ != 0:
                    username = self.names_email_lookup.get_field_by_name(
                        names_and_email, "username"
                    )
                    old_saml_id = cast(
                        str,
                        self.names_email_lookup.get_field_by_name(
                            names_and_email, "saml_id"
                        ),
                    )
                    old_default_password = cast(
                        str,
                        self.names_email_lookup.get_field_by_name(
                            names_and_email, "default_password"
                        ),
                    )
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

        if saml_id := entry.get("saml_id"):
            check_result = self.all_saml_id_lookup.check_duplicate(saml_id)
            if id_ := entry.get("id"):
                if check_result == ResultType.FOUND_ID:
                    idFound = self.all_saml_id_lookup.get_field_by_name(saml_id, "id")
                if check_result == ResultType.NOT_FOUND or (
                    check_result == ResultType.FOUND_ID and id_ == idFound
                ):
                    entry["saml_id"] = {
                        "value": saml_id,
                        "info": (
                            ImportState.DONE if old_saml_id else ImportState.NEW
                        ),  # only if newly set
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
            if (
                entry["saml_id"]["info"] == ImportState.NEW
                or entry.get("default_password")
                or old_default_password
            ):
                entry["default_password"] = {"value": "", "info": ImportState.WARNING}
                messages.append(
                    f"Because this {self.import_name} is connected with a saml_id: The default_password will be ignored and password will not be changeable in OpenSlides."
                )
        else:
            self.handle_default_password(entry)

        if gender := entry.get("gender"):
            try:
                check_gender_helper(self.datastore, entry)
                entry["gender"] = {"info": ImportState.DONE, "value": gender}
            except ActionException:
                entry["gender"] = {"info": ImportState.WARNING, "value": gender}
                messages.append(f"Gender '{gender}' is not in the allowed gender list.")

        return {"state": self.row_state, "messages": messages, "data": entry}

    def create_usernames(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        usernames: List[str] = []
        fix_usernames: List[str] = []
        payload_indices: List[int] = []

        for entry in data:
            if "username" not in entry.keys():
                if saml_id := entry.get("saml_id"):
                    username = saml_id
                else:
                    username = self.generate_username(entry)
                usernames.append(username)
                payload_indices.append(entry["payload_index"])
            else:
                fix_usernames.append(entry["username"])

        usernames = self.generate_usernames(usernames, fix_usernames)

        for index, username in zip(payload_indices, usernames):
            data[index]["username"] = {
                "value": username,
                "info": ImportState.GENERATED,
            }
            self.username_lookup.add_item(data[index])
        return data

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

    def setup_lookups(
        self, data: List[Dict[str, Any]], meeting_id: Optional[int] = None
    ) -> None:
        self.username_lookup = Lookup(
            self.datastore,
            "user",
            [
                (username, entry)
                for entry in data
                if (username := entry.get("username"))
            ],
            field="username",
            mapped_fields=["username", "saml_id", "default_password"],
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
            mapped_fields=["saml_id", "username", "default_password"],
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
            field=("first_name", "last_name", "email"),
            mapped_fields=["username", "saml_id", "default_password"],
        )
        self.all_saml_id_lookup = Lookup(
            self.datastore,
            "user",
            [(saml_id, entry) for entry in data if (saml_id := entry.get("saml_id"))],
            field="saml_id",
            mapped_fields=["username", "saml_id"],
        )

        self.all_id_mapping: Dict[int, List[SearchFieldType]] = defaultdict(list)
        for lookup in (
            self.username_lookup,
            self.saml_id_lookup,
            self.names_email_lookup,
        ):
            for id, values in lookup.id_to_name.items():
                self.all_id_mapping[id].extend(values)

    def distribute_found_value_to_data(self, data: List[Dict[str, Any]]) -> None:
        for entry in data:
            if "username" in entry:
                continue
            if "saml_id" in entry:
                lookup_result = self.saml_id_lookup.name_to_ids[entry["saml_id"]][0]
            else:
                key = (
                    entry.get("first_name", ""),
                    entry.get("last_name", ""),
                    entry.get("email", ""),
                )
                lookup_result = self.names_email_lookup.name_to_ids[key][0]
            if not (id_ := lookup_result.get("id")):
                continue
            if "id" not in entry:
                entry["id"] = id_
            if "username" not in entry:
                entry["username"] = {
                    "id": id_,
                    "value": lookup_result["username"],
                    "info": ImportState.DONE,
                }
                self.username_lookup.add_item(entry)
