from typing import Any, cast

from openslides_backend.services.datastore.commands import GetManyRequest

from ....permissions.management_levels import CommitteeManagementLevel
from ....permissions.permission_helper import has_committee_management_level
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.import_mixins import BaseImportAction, ImportRow, ImportState, Lookup
from ...util.typing import ActionResults
from .create import UserCreate
from .update import UserUpdate


class BaseUserImport(BaseImportAction):
    """
    Action to import a result from the action_worker.
    """

    skip_archived_meeting_check = True

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        super().update_instance(instance)
        self.setup_lookups()
        for row in self.rows:
            self.validate_entry(row)

        self.check_all_rows()

        self.handle_create_relations(instance)
        if self.import_state != ImportState.ERROR:
            rows = self.flatten_copied_object_fields(
                self.handle_remove_and_group_fields
            )
            self.create_other_actions(rows)

        return {}

    def check_all_rows(self) -> None:
        """
        Function for bulk-checks of the import rows after validation via 'validate_entry'.
        Should be overwritten by subclasses if it is required.
        """

    def handle_create_relations(self, instance: dict[str, Any]) -> None:
        pass

    def handle_remove_and_group_fields(self, entry: dict[str, Any]) -> dict[str, Any]:
        for field in ("groups", "structure_level"):
            if field in entry and (instances := entry.pop(field)):
                relation_field = field.rstrip("s") + "_ids"
                entry[relation_field] = [
                    id_ for instance in instances if (id_ := instance.get("id"))
                ]
        if (
            "home_committee" in entry
            and entry["home_committee"]["info"] != ImportState.REMOVE
            and (instance := entry.pop("home_committee"))
        ):
            if home_committee_id := instance.get("id"):
                entry["home_committee_id"] = home_committee_id

        # set fields empty/False if saml_id will be set
        field_values = (
            ("can_change_own_password", False),
            ("default_password", ""),
        )
        username = cast(str, self.get_value_from_union_str_object(entry["username"]))
        member_number = self.get_value_from_union_str_object(entry.get("member_number"))
        if (
            (obj := entry.get("saml_id"))
            and obj["value"]
            and obj["info"] != ImportState.REMOVE
        ):
            for field, value in field_values:
                field_data = self.username_lookup.get_field_by_name(username, field)
                if member_number:
                    field_data = (
                        self.member_number_lookup.get_field_by_name(
                            member_number, field
                        )
                        or field_data
                    )
                if field_data or entry.get(field):
                    entry[field] = value
        if isinstance(entry.get("gender"), dict):
            if entry["gender"].get("info") != ImportState.WARNING:
                entry["gender_id"] = entry["gender"]["id"]
            entry.pop("gender")

        # remove all fields marked with "remove"-state
        to_remove = []
        for k, v in entry.items():
            if isinstance(v, dict):
                if v.get("info") == ImportState.REMOVE:
                    to_remove.append(k)
        for k in to_remove:
            entry.pop(k)
        return entry

    def create_other_actions(self, rows: list[ImportRow]) -> list[int | None]:
        create_action_payload: list[dict[str, Any]] = []
        update_action_payload: list[dict[str, Any]] = []
        index_to_is_create: list[bool] = []
        for row in rows:
            if row["state"] == ImportState.NEW:
                create_action_payload.append(row["data"])
                index_to_is_create.append(True)
            else:
                if " " in row["data"].get("username", ""):
                    row["data"].pop("username", None)
                update_action_payload.append(row["data"])
                index_to_is_create.append(False)
        create_results: ActionResults | None = []
        update_results: ActionResults | None = []
        if create_action_payload:
            create_results = self.execute_other_action(
                UserCreate, create_action_payload
            )
        if update_action_payload:
            update_results = self.execute_other_action(
                UserUpdate, update_action_payload
            )
        ids: list[int | None] = []
        for is_create in index_to_is_create:
            if is_create:
                result = create_results.pop(0) if create_results else None
            else:
                result = update_results.pop(0) if update_results else None
            ids.append(result.get("id") if isinstance(result, dict) else None)
        return ids

    def validate_entry(self, row: ImportRow) -> None:
        if not (
            row["state"] == ImportState.DONE
            and row["data"].get("username", {}).get("info") == ImportState.NEW
        ):
            id = self.validate_with_lookup(row, self.username_lookup, "username")
            self.validate_with_lookup(
                row, self.member_number_lookup, "member_number", False, id
            )
        else:
            id = self.validate_with_lookup(
                row, self.member_number_lookup, "member_number"
            )
            self.validate_with_lookup(row, self.username_lookup, "username", False, id)
        self.validate_with_lookup(row, self.saml_id_lookup, "saml_id", False, id)
        self.validate_field(row, self.committee_map, "home_committee", False)
        if (row["data"].get("id")) and (
            old_home_committee_id := self.datastore.get(
                fqid_from_collection_and_id("user", (row["data"]["id"])),
                ["home_committee_id"],
                raise_exception=False,
            ).get("home_committee_id")
        ):
            old_hc_permission = has_committee_management_level(
                self.datastore,
                self.user_id,
                CommitteeManagementLevel.CAN_MANAGE,
                old_home_committee_id,
            )
        else:
            old_hc_permission = True
        if (
            (
                home_committee_id := (
                    home_committee := row["data"].get("home_committee", {})
                ).get("id")
            )
            and home_committee["info"] == ImportState.DONE
            and (
                not old_hc_permission
                or not has_committee_management_level(
                    self.datastore,
                    self.user_id,
                    CommitteeManagementLevel.CAN_MANAGE,
                    home_committee_id,
                )
            )
        ):
            row["data"]["home_committee"] = {
                "id": home_committee["id"],
                "value": home_committee["value"],
                "info": ImportState.ERROR,
            }
            row["state"] = ImportState.ERROR
            row["messages"].append(
                "Error: No longer permitted to change the home committee."
            )
        if (
            not old_hc_permission
            and row["data"].get("guest", {}).get("value") != ImportState.REMOVE
            and (guest := row["data"].get("guest", {}).get("value")) is True
            and row["data"].get("guest", {}).get("info") == ImportState.DONE
        ):
            row["data"]["guest"] = {
                "value": guest,
                "info": ImportState.ERROR,
            }
            row["state"] = ImportState.ERROR
            row["messages"].append(
                "Error: No longer permitted to set guest to true: Insufficient rights for unsetting the home committee."
            )

        if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
            self.import_state = ImportState.ERROR

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
        self.member_number_lookup = Lookup(
            self.datastore,
            "user",
            [
                (entry["member_number"]["value"], entry)
                for row in self.rows
                if "member_number" in (entry := row["data"])
            ],
            field="member_number",
            mapped_fields=[
                "default_password",
                "can_change_own_password",
            ],
        )
        result = self.datastore.get_many(
            [
                GetManyRequest(
                    "committee",
                    [
                        id
                        for row in self.rows
                        if (id := row["data"].get("home_committee", {}).get("id"))
                    ],
                    ["name"],
                ),
            ],
            lock_result=False,
            use_changed_models=False,
        )
        self.committee_map = {
            k: v["name"] for k, v in result.get("committee", {}).items()
        }
