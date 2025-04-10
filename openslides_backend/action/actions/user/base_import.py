from typing import Any, cast

from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.shared.mixins.user_create_update_permissions_mixin import (
    CreateUpdatePermissionsFailingFields,
    PermissionVarStore,
)

from ...mixins.import_mixins import BaseImportAction, ImportRow, ImportState, Lookup
from ...util.typing import ActionResults
from .create import UserCreate
from .update import UserUpdate


class BaseUserImport(BaseImportAction):
    """
    Action to import a result from the action_worker.
    """

    skip_archived_meeting_check = True

    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)

        permstore = PermissionVarStore(self.datastore, self.user_id)
        self.permission_check = CreateUpdatePermissionsFailingFields(
            self.user_id,
            permstore,
            self.services,
            self.datastore,
            self.relation_manager,
            self.logging,
            self.env,
            self.skip_archived_meeting_check,
            self.use_meeting_ids_for_archived_meeting_check,
        )

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

        # if row["state"] == ImportState.ERROR and self.import_state == ImportState.DONE:
        #     self.import_state = ImportState.ERROR

    def check_field_failures(
        self, entry: dict[str, Any], messages: list[str], groups: str = "ABDEFGHIJ"
    ) -> bool:
        if home_committee := entry.pop("home_committee", None):
            entry["home_committee_id"] = home_committee
        failing_fields_jsonupload = {
            field
            for field in entry
            if isinstance(entry[field], dict)
            and entry[field]["info"] == ImportState.REMOVE
        }
        if home_committee:
            entry["home_committee_id"] = home_committee.get("id")

        failing_fields = self.permission_check.get_failing_fields(entry, groups)
        if home_committee:
            entry["home_committee"] = home_committee
            entry.pop("home_committee_id")
        if less_ff := list(failing_fields_jsonupload - set(failing_fields)):
            less_ff.sort()
            messages.append(
                f"In contrast to preview you may import field(s) '{', '.join(less_ff)}'"
            )
            for field in less_ff:
                actual_field = (
                    field[:-3]
                    if field not in entry and field.endswith("_id")
                    else field
                )
                entry[actual_field]["info"] = ImportState.DONE
        if more_ff := list(set(failing_fields) - failing_fields_jsonupload):
            more_ff.sort()
            messages.append(
                f"Error: In contrast to preview you may not import field(s) '{', '.join(more_ff)}'"
            )
            for field in more_ff:
                actual_field = (
                    field[:-3]
                    if field not in entry and field.endswith("_id")
                    else field
                )
                entry[actual_field]["info"] = ImportState.ERROR
            return False
        return True

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
