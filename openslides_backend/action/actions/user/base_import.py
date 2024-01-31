from typing import Any, Dict, List, Optional, cast

from ...mixins.import_mixins import BaseImportAction, ImportRow, ImportState, Lookup
from ...util.typing import ActionResults
from .create import UserCreate
from .update import UserUpdate


class BaseUserImport(BaseImportAction):
    """
    Action to import a result from the action_worker.
    """

    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        super().update_instance(instance)
        self.setup_lookups()
        for row in self.rows:
            self.validate_entry(row)

        if self.import_state != ImportState.ERROR:
            rows = self.flatten_copied_object_fields(
                self.handle_remove_email_and_group_fields
            )
            self.create_other_actions(rows)

        return {}

    def handle_remove_email_and_group_fields(
        self, entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        if (groups := entry.pop("groups", None)) is not None:
            entry["group_ids"] = [id_ for group in groups if (id_ := group.get("id"))]

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

        if (email := entry.get("email")) and email["info"] == ImportState.WARNING:
            entry.pop("email")

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

    def validate_entry(self, row: ImportRow) -> None:
        id = self.validate_with_lookup(row, self.username_lookup, "username")
        self.validate_with_lookup(row, self.saml_id_lookup, "saml_id", False, id)
        if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR

        return row

    def setup_lookups(self) -> None:
        self.username_lookup = Lookup(
            self.datastore,
            "user",
            [
                (entry["username"]["value"], entry)
                for row in self.rows
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
                for row in self.rows
                if "saml_id" in (entry := row["data"])
            ],
            field="saml_id",
        )
