from collections import defaultdict
from typing import Any, cast

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.import_mixins import (
    BaseJsonUploadAction,
    ImportState,
    Lookup,
    ResultType,
    SearchFieldType,
)
from ...mixins.send_email_mixin import EmailUtils
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
        {"property": "email", "type": "string", "is_object": True},
        {"property": "username", "type": "string", "is_object": True},
        {"property": "gender", "type": "string", "is_object": True},
        {"property": "pronoun", "type": "string"},
        {"property": "saml_id", "type": "string", "is_object": True},
        {"property": "member_number", "type": "string", "is_object": True},
    ]
    skip_archived_meeting_check = True
    row_state: ImportState
    username_lookup: Lookup
    saml_id_lookup: Lookup
    names_email_lookup: Lookup
    all_saml_id_lookup: Lookup
    member_number_lookup: Lookup

    @classmethod
    def get_schema(
        cls,
        additional_user_fields: dict[str, Any],
        additional_required_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
                                "member_number",
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

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        data = instance.pop("data")
        data = self.add_payload_index_to_action_data(data)
        self.setup_lookups(data)
        self.distribute_found_value_to_data(data)
        self.create_usernames(data)

        self.rows = [self.validate_entry(entry) for entry in data]
        self.generate_statistics()
        return {}

    def validate_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        messages: list[str] = []
        id_: int | None = None
        old_saml_id: str | None = None
        old_default_password: str | None = None
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
                if isinstance(username, str):
                    entry["username"] = {
                        "value": username,
                        "info": ImportState.DONE,
                        "id": id_,
                    }
            elif check_result == ResultType.NOT_FOUND or id_ == 0:
                self.row_state = ImportState.NEW
        else:
            if not entry.get("username") or (
                not isinstance(entry.get("username"), str)
                and not entry.get("username", {}).get("value")
            ):
                self.row_state = ImportState.ERROR
                messages.append(
                    "Cannot generate username. Missing one of first_name, last_name or a unique member_number."
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
                        "value": (
                            cast(dict, username).get("value")
                            if isinstance(username, dict)
                            else username
                        ),
                        "info": ImportState.DONE,
                        "id": id_,
                    }
                elif check_result == ResultType.NOT_FOUND or id_ == 0:
                    self.row_state = ImportState.NEW
                elif check_result == ResultType.FOUND_MORE_IDS:
                    self.row_state = ImportState.ERROR
                    messages.append("Found more users with name and email")

        if member_number := entry.get("member_number"):
            check_result = self.member_number_lookup.check_duplicate(member_number)
            member_id = cast(
                int, self.member_number_lookup.get_field_by_name(member_number, "id")
            )
            if id_ and self.row_state == ImportState.DONE:
                oldnum = self.datastore.get(
                    fqid_from_collection_and_id("user", id_), ["member_number"]
                ).get("member_number")
                has_member_number_error = False

                if oldnum and member_number != oldnum:
                    has_member_number_error = True
                    messages.append("Error: Member numbers can't be updated via import")
                elif member_id and member_id != id_:
                    has_member_number_error = True
                    messages.append("Error: Member number doesn't match detected user")
                elif check_result == ResultType.FOUND_MORE_IDS:
                    has_member_number_error = True
                    messages.append(
                        "Error: Found more users with the same member number"
                    )

                if has_member_number_error:
                    self.row_state = ImportState.ERROR
                    entry["member_number"] = {
                        "value": member_number,
                        "info": ImportState.ERROR,
                    }
                else:
                    entry["member_number"] = {
                        "value": member_number,
                        "info": ImportState.DONE if oldnum else ImportState.NEW,
                    }
                    if oldnum:
                        entry["member_number"]["id"] = id_
                        entry["username"].pop("id")
            elif not id_:
                id_ = member_id
                if check_result == ResultType.FOUND_ID and id_ != 0:
                    old_username = cast(
                        str,
                        self.member_number_lookup.get_field_by_name(
                            member_number, "username"
                        ),
                    )
                    entry["id"] = id_
                    entry["member_number"] = {
                        "id": id_,
                        "value": member_number,
                        "info": ImportState.DONE,
                    }
                    if not entry.get("username"):
                        entry["username"] = {
                            "value": old_username,
                            "info": ImportState.DONE,
                        }
                    elif (
                        entry["username"] != old_username
                        and entry["username"]["info"] == ImportState.DONE
                    ):
                        entry["username"]["info"] = ImportState.NEW
                    if self.row_state != ImportState.ERROR:
                        self.row_state = ImportState.DONE
                elif check_result == ResultType.FOUND_MORE_IDS:
                    self.row_state = ImportState.ERROR
                    entry["member_number"] = {
                        "value": member_number,
                        "info": ImportState.ERROR,
                    }
                    messages.append(
                        "Error: Found more users with the same member number"
                    )
                else:
                    entry["member_number"] = {
                        "value": member_number,
                        "info": ImportState.DONE,
                    }

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

        if email := entry.get("email"):
            if EmailUtils.check_email(email):
                entry["email"] = {"info": ImportState.DONE, "value": email}
            else:
                entry["email"] = {"info": ImportState.ERROR, "value": email}
                self.row_state = ImportState.ERROR
                messages.append(f"Error: '{email}' is not a valid email address.")

        return {"state": self.row_state, "messages": messages, "data": entry}

    def create_usernames(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        usernames: list[str] = []
        fix_usernames: list[str] = []
        payload_indices: list[int] = []
        memnum_payload_indices: list[int] = []
        memnum_usernames: list[str] = []

        for entry in data:
            if "username" not in entry.keys():
                if saml_id := entry.get("saml_id"):
                    username = saml_id
                else:
                    username = self.generate_username(entry)
                if (
                    not username
                    and (memnum := entry.get("member_number"))
                    and not self.datastore.exists(
                        "user", FilterOperator("username", "=", memnum)
                    )
                ):
                    memnum_usernames.append(memnum)
                    memnum_payload_indices.append(entry["payload_index"])
                else:
                    usernames.append(username)
                    payload_indices.append(entry["payload_index"])
            else:
                fix_usernames.append(entry["username"])

        usernames = self.generate_usernames(usernames, fix_usernames + memnum_usernames)

        for index, username in zip(payload_indices, usernames):
            data[index]["username"] = {
                "value": username,
                "info": ImportState.GENERATED,
            }
            self.username_lookup.add_item(data[index])
        for index, username in zip(memnum_payload_indices, memnum_usernames):
            data[index]["username"] = {
                "value": username if username not in fix_usernames else "",
                "info": ImportState.GENERATED,
            }
            self.username_lookup.add_item(data[index])
        return data

    def handle_default_password(self, entry: dict[str, Any]) -> None:
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
    def _names_and_email(entry: dict[str, Any]) -> tuple[str, ...]:
        return (
            entry.get("first_name", ""),
            entry.get("last_name", ""),
            entry.get("email", ""),
        )

    def setup_lookups(self, data: list[dict[str, Any]]) -> None:
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
        self.member_number_lookup = Lookup(
            self.datastore,
            "user",
            [
                (member_number, entry)
                for entry in data
                if (member_number := entry.get("member_number"))
            ],
            field="member_number",
            mapped_fields=["username", "member_number", "saml_id"],
        )

        self.all_id_mapping: dict[int, list[SearchFieldType]] = defaultdict(list)
        for lookup in (
            self.username_lookup,
            self.saml_id_lookup,
            self.names_email_lookup,
        ):
            for id, values in lookup.id_to_name.items():
                self.all_id_mapping[id].extend(values)

    def distribute_found_value_to_data(self, data: list[dict[str, Any]]) -> None:
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
            if "member_number" in entry:
                lookup_result = (
                    self.member_number_lookup.name_to_ids[entry["member_number"]][0]
                    or lookup_result
                )
            if not (id_ := lookup_result.get("id")):
                continue
            if "id" not in entry:
                entry["id"] = id_
            if "username" not in entry:
                username = lookup_result["username"]
                entry["username"] = {
                    "id": id_,
                    "value": (
                        username if isinstance(username, str) else username["value"]
                    ),
                    "info": ImportState.DONE,
                }
                self.username_lookup.add_item(entry)
