from typing import Any, Dict, List, cast

from ....models.models import ActionWorker
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import ImportMixin, ImportRow, ImportState, Lookup, ResultType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import UserCreate
from .update import UserUpdate
from .user_mixin import DuplicateCheckMixin


@register_action("account.import")
class AccountImport(DuplicateCheckMixin, ImportMixin):
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

            for row in self.rows:
                if row["state"] == ImportState.DONE:
                    create_action_payload.append(row["data"])
                else:
                    update_action_payload.append(row["data"])
                if create_action_payload:
                    self.execute_other_action(UserCreate, create_action_payload)
                if update_action_payload:
                    self.execute_other_action(UserUpdate, update_action_payload)

        return {}


    def validate_entry(self, row: Dict[str, Dict[str, Any]]) -> ImportRow:
        entry = row["data"]
        username = self.get_value_from_union_str_object(entry.get("username"))
        check_result = self.username_lookup.check_duplicate(username)
        id_ = cast(int, self.username_lookup.get_field_by_name(username, "id"))

        if check_result == ResultType.FOUND_ID and id_ != 0:
            if row["state"] != ImportState.DONE:
                entry["messages"].append(f"error: row state expected to be 'DONE', but it is '{row['state']}'.")
                row["state"] = ImportState.ERROR
                entry["username"]["info"] = ImportState.ERROR
            elif entry["id"] != id_:
                row["state"] = ImportState.ERROR
                entry["username"]["info"] = ImportState.ERROR
                entry["messages"].append(f"error: username '{username}' found in different id ({id_} instead of {entry['id']})")
        elif check_result == ResultType.FOUND_MORE_IDS:
            row["state"] = ImportState.ERROR
            entry["username"]["info"] = ImportState.ERROR
            entry["messages"].append(f"error: username '{username}' is duplicated in import.")
        elif check_result == ResultType.NOT_FOUND:
            if row["state"] != ImportState.NEW:
                entry["messages"].append(f"error: row state expected to be 'NEW', but it is '{row['state']}'.")
                row["state"] = ImportState.ERROR

        saml_id = self.get_value_from_union_str_object(entry.get("saml_id"))
        if saml_id:
            check_result = self.saml_id_lookup.check_duplicate(saml_id)
            id_from_saml_id = cast(int, self.saml_id_lookup.get_field_by_name(saml_id, "id"))
            if check_result == ResultType.FOUND_ID and id_ != 0:
                if id_ != id_from_saml_id:
                    row["state"] = ImportState.ERROR
                    entry["saml_id"]["info"] = ImportState.ERROR
                    entry["messages"].append(f"error: saml_id '{saml_id}' found in different id ({id_from_saml_id} instead of {id_})")
            elif check_result == ResultType.FOUND_MORE_IDS:
                row["state"] = ImportState.ERROR
                entry["saml_id"]["info"] = ImportState.ERROR
                entry["messages"].append(f"error: saml_id '{saml_id}' is duplicated in import.")

            if (default_password := entry.get("default_password")) and type(default_password) == dict and default_password["info"] == ImportState.WARNING:
                for field in ("password", "can_change_own_password"):
                    value = self.username_lookup.get_field_by_name(username, field)
                    if value:
                        if field == "can_change_own_password":
                            entry[field] = False
                        else:
                            entry[field] = ""
        if not self.error and row["state"] == ImportState.ERROR:
            self.error = True
        return { "state": row["state"], "data": row["data"], "messages": row.get("messages", [])}

    def setup_lookups(self) -> None:
        rows = self.result["rows"]
        self.username_lookup = Lookup(
            self.datastore,
            "user",
            [
                ((entry := row["data"])["username"]["value"], entry)
                for row in rows
            ],
            field="username",
            mapped_fields=["saml_id", "default_password", "password", "can_change_own_password"],
        )
        self.saml_id_lookup = Lookup(
            self.datastore,
            "user",
            [
                (entry["saml_id"]["value"], entry)
                for row in rows
                if "saml_id" in (entry :=row["data"])
            ],
            field="saml_id",
        )

    def xupdate_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)

        # handle abort in on_success
        if not instance["import"]:
            return {}

        # init duplicate mixin
        data = self.result.get("rows", [])
        for entry in data:
            # Revert username-info and default-password-info
            for field in ("username", "default_password", "saml_id"):
                if field in entry["data"]:
                    if field == "username" and "id" in entry["data"][field]:
                        entry["data"]["id"] = entry["data"][field]["id"]
                    if type(dvalue := entry["data"][field]) == dict:
                        entry["data"][field] = dvalue["value"]

        search_data_list = [
            {
                field: entry["data"].get(field, "")
                for field in ("username", "first_name", "last_name", "email", "saml_id")
            }
            for entry in data
        ]
        self.init_duplicate_set(search_data_list)

        # Recheck and update data, update needs "id"
        create_action_payload: List[Dict[str, Any]] = []
        update_action_payload: List[Dict[str, Any]] = []
        self.error = False
        for payload_index, entry in enumerate(data):
            if entry["state"] == ImportState.NEW:
                if not entry["data"].get("username") and not entry["data"].get(
                    "saml_id"
                ):
                    self.error = True
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Error: Want to create user, but missing username in import data."
                    )
                elif entry["data"].get(
                    "username"
                ) and self.check_username_for_duplicate(
                    entry["data"]["username"], payload_index
                ):
                    self.error = True
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Error: want to create a new user, but username already exists."
                    )
                elif entry["data"].get("saml_id") and self.check_saml_id_for_duplicate(
                    entry["data"]["saml_id"], payload_index
                ):
                    self.error = True
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Error: want to create a new user, but saml_id already exists."
                    )
                else:
                    create_action_payload.append(entry["data"])
            elif entry["state"] == ImportState.DONE:
                search_data = self.get_search_data(payload_index)
                if not entry["data"].get("username") and not entry["data"].get(
                    "saml_id"
                ):
                    self.error = True
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Error: Want to update user, but missing username in import data."
                    )
                elif entry["data"].get(
                    "username"
                ) and not self.check_username_for_duplicate(
                    entry["data"]["username"], payload_index
                ):
                    self.error = True
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Error: want to update, but missing user in db."
                    )
                elif entry["data"].get(
                    "saml_id"
                ) and not self.check_saml_id_for_duplicate(
                    entry["data"]["saml_id"], payload_index
                ):
                    self.error = True
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Error: want to update, but missing user in db."
                    )
                elif search_data is None:
                    self.error = True
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Error: want to update, but found search data are wrong."
                    )
                elif search_data["id"] != entry["data"]["id"]:
                    self.error = True
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Error: want to update, but found search data doesn't match."
                    )
                else:
                    if "username" in entry["data"]:
                        del entry["data"]["username"]
                    update_action_payload.append(entry["data"])
            else:
                self.error = True
                entry["messages"].append("Error in import.")

        # execute the actions
        if not self.error:
            if create_action_payload:
                self.execute_other_action(UserCreate, create_action_payload)
            if update_action_payload:
                self.execute_other_action(UserUpdate, update_action_payload)
        else:
            self.error_store_ids.append(instance["id"])
        return {}
