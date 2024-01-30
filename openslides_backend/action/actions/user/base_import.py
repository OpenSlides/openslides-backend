from typing import Any, Dict, List, Optional, cast

from ....shared.exceptions import ActionException
from ...mixins.import_mixins import (
    ImportMixin,
    ImportRow,
    ImportState,
    Lookup,
    ResultType,
)
from ...util.typing import ActionData, ActionResults
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

        self.handle_create_relations(instance)
        if self.import_state != ImportState.ERROR:
            rows = self.flatten_copied_object_fields(
                self.handle_remove_and_group_fields
            )
            self.create_other_actions(rows)

        return {}

    def handle_create_relations(self, instance: Dict[str, Any]) -> None:
        pass

    def handle_remove_and_group_fields(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        for field in ("groups", "structure_level"):
            if field in entry and (instances := entry.pop(field)):
                relation_field = field.rstrip("s") + "_ids"
                entry[relation_field] = [
                    id_ for instance in instances if (id_ := instance.get("id"))
                ]

        # set fields empty/False if saml_id will be set
        field_values = (
            ("can_change_own_password", False),
            ("default_password", ""),
        )
        username = cast(str, self.get_value_from_union_str_object(entry["username"]))
        if (
            (obj := entry.get("saml_id"))
            and obj["value"]
            and obj["info"] != ImportState.REMOVE
        ):
            for field, value in field_values:
                if self.username_lookup.get_field_by_name(username, field) or entry.get(
                    field
                ):
                    entry[field] = value

        if (
            isinstance(entry.get("gender"), dict)
            and entry["gender"].get("info") == ImportState.WARNING
        ):
            entry.pop("gender")

        # remove all fields fields marked with "remove"-state
        to_remove = []
        for k, v in entry.items():
            if isinstance(v, dict):
                if v.get("info") == ImportState.REMOVE:
                    to_remove.append(k)
        for k in to_remove:
            entry.pop(k)
        return entry

    def create_other_actions(self, rows: List[ImportRow]) -> List[Optional[int]]:
        create_action_payload: List[Dict[str, Any]] = []
        update_action_payload: List[Dict[str, Any]] = []
        index_to_is_create: List[bool] = []
        for row in rows:
            if row["state"] == ImportState.NEW:
                create_action_payload.append(row["data"])
                index_to_is_create.append(True)
            else:
                update_action_payload.append(row["data"])
                index_to_is_create.append(False)
        create_results: Optional[ActionResults] = []
        update_results: Optional[ActionResults] = []
        if create_action_payload:
            create_results = self.execute_other_action(
                UserCreate, create_action_payload
            )
        if update_action_payload:
            update_results = self.execute_other_action(
                UserUpdate, update_action_payload
            )
        ids: List[Optional[int]] = []
        for is_create in index_to_is_create:
            if is_create:
                result = create_results.pop(0) if create_results else None
            else:
                result = update_results.pop(0) if update_results else None
            ids.append(result.get("id") if isinstance(result, dict) else None)
        return ids

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
