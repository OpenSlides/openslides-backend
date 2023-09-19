from typing import Any, Dict, List, cast

from ....models.models import ActionWorker
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.exceptions import ActionException
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import (
    ImportMixin,
    ImportRow,
    ImportState,
    Lookup,
    ResultType,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import UserCreate
from .update import UserUpdate


@register_action("account.import")
class AccountImport(ImportMixin):
    """
    Action to import a result from the action_worker.
    """

    model = ActionWorker()
    schema = DefaultSchema(ActionWorker()).get_default_schema(
        additional_required_fields={
            "id": required_id_schema,
            "import": {"type": "boolean"},
        }
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_USERS
    skip_archived_meeting_check = True
    import_name = "account"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if not instance["import"]:
            return {}

        instance = super().update_instance(instance)
        self.error = False
        self.setup_lookups()

        self.rows = [self.validate_entry(row) for row in self.result["rows"]]

        if self.error:
            self.error_store_ids.append(instance["id"])
        else:
            create_action_payload: List[Dict[str, Any]] = []
            update_action_payload: List[Dict[str, Any]] = []
            self.flatten_object_fields(["username", "saml_id", "default_password"])
            for row in self.rows:
                if row["state"] == ImportState.NEW:
                    create_action_payload.append(row["data"])
                else:
                    update_action_payload.append(row["data"])
            if create_action_payload:
                self.execute_other_action(UserCreate, create_action_payload)
            if update_action_payload:
                self.execute_other_action(UserUpdate, update_action_payload)

        return {}

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
        if not self.error and row["state"] == ImportState.ERROR:
            self.error = True
        return {
            "state": row["state"],
            "data": row["data"],
            "messages": row.get("messages", []),
        }

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
