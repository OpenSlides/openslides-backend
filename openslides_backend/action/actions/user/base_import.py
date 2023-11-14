from typing import Any, Dict, List, cast

from ....shared.exceptions import ActionException
from ...mixins.import_mixins import (
    ImportMixin,
    ImportRow,
    ImportState,
    Lookup,
    ResultType,
)
from ...util.typing import ActionData
from .create import UserCreate
from .update import UserUpdate


class BaseUserImport(ImportMixin):
    """
    Action to import a result from the action_worker.
    """

    skip_archived_meeting_check = True

    def prefetch(self, action_data: ActionData) -> None:
        super().prefetch(action_data)
        self.rows = self.result["rows"]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        if not instance["import"]:
            return {}

        self.setup_lookups()

        self.rows = [self.validate_entry(row) for row in self.rows]

        if self.import_state != ImportState.ERROR:
            rows = self.flatten_copied_object_fields()
            self.create_other_actions(rows)

        return {}

    def create_other_actions(self, rows: List[ImportRow]) -> None:
        create_action_payload: List[Dict[str, Any]] = []
        update_action_payload: List[Dict[str, Any]] = []
        for row in rows:
            if row["state"] == ImportState.NEW:
                create_action_payload.append(row["data"])
            else:
                update_action_payload.append(row["data"])
        if create_action_payload:
            self.execute_other_action(UserCreate, create_action_payload)
        if update_action_payload:
            self.execute_other_action(UserUpdate, update_action_payload)

    def validate_entry(self, row: ImportRow) -> ImportRow:
        entry = row["data"]
        username = self.get_value_from_union_str_object(entry.get("username"))
        if not username:
            raise ActionException(
                "Invalid JsonUpload data: The data from json upload must contain a valid username object"
            )
        check_result = self.username_lookup.check_duplicate(username)
        id_ = cast(int, self.username_lookup.get_field_by_name(username, "id"))

        if check_result == ResultType.FOUND_ID and id_ != 0:
            if row["state"] != ImportState.DONE:
                row["messages"].append(
                    f"Error: row state expected to be '{ImportState.DONE}', but it is '{row['state']}'."
                )
                row["state"] = ImportState.ERROR
                entry["username"]["info"] = ImportState.ERROR
            elif "id" not in entry:
                raise ActionException(
                    f"Invalid JsonUpload data: A data row with state '{ImportState.DONE}' must have an 'id'"
                )
            elif entry["id"] != id_:
                row["state"] = ImportState.ERROR
                entry["username"]["info"] = ImportState.ERROR
                row["messages"].append(
                    f"Error: username '{username}' found in different id ({id_} instead of {entry['id']})"
                )
        elif check_result == ResultType.FOUND_MORE_IDS:
            row["state"] = ImportState.ERROR
            entry["username"]["info"] = ImportState.ERROR
            row["messages"].append(
                f"Error: username '{username}' is duplicated in import."
            )
        elif check_result == ResultType.NOT_FOUND_ANYMORE:
            row["messages"].append(
                f"Error: user {entry['username']['id']} not found anymore for updating user '{username}'."
            )
            row["state"] = ImportState.ERROR
        elif check_result == ResultType.NOT_FOUND:
            pass  # cannot create an error !

        saml_id = self.get_value_from_union_str_object(entry.get("saml_id"))
        if saml_id:
            check_result = self.saml_id_lookup.check_duplicate(saml_id)
            id_from_saml_id = cast(
                int, self.saml_id_lookup.get_field_by_name(saml_id, "id")
            )
            if check_result == ResultType.FOUND_ID and id_ != 0:
                if id_ != id_from_saml_id:
                    row["state"] = ImportState.ERROR
                    entry["saml_id"]["info"] = ImportState.ERROR
                    row["messages"].append(
                        f"Error: saml_id '{saml_id}' found in different id ({id_from_saml_id} instead of {id_})"
                    )
            elif check_result == ResultType.FOUND_MORE_IDS:
                row["state"] = ImportState.ERROR
                entry["saml_id"]["info"] = ImportState.ERROR
                row["messages"].append(
                    f"Error: saml_id '{saml_id}' is duplicated in import."
                )
            elif check_result == ResultType.NOT_FOUND_ANYMORE:
                row["state"] = ImportState.ERROR
                entry["saml_id"]["info"] = ImportState.ERROR
                row["messages"].append(
                    f"Error: saml_id '{saml_id}' not found anymore in user with id '{id_from_saml_id}'"
                )
            elif check_result == ResultType.NOT_FOUND:
                pass

            if (
                (default_password := entry.get("default_password"))
                and type(default_password) == dict
                and default_password["info"] == ImportState.WARNING
            ):
                field = "can_change_own_password"
                if self.username_lookup.get_field_by_name(username, field):
                    entry[field] = False
        if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR
        return row

    def setup_lookups(self) -> None:
        rows = self.result["rows"]
        self.username_lookup = Lookup(
            self.datastore,
            "user",
            [
                (entry["username"]["value"], entry)
                for row in rows
                if "username" in (entry := row["data"])
            ],
            field="username",
            mapped_fields=[
                "saml_id",
                "default_password",
                "password",
                "can_change_own_password",
            ],
        )
        self.saml_id_lookup = Lookup(
            self.datastore,
            "user",
            [
                (entry["saml_id"]["value"], entry)
                for row in rows
                if "saml_id" in (entry := row["data"])
            ],
            field="saml_id",
        )
