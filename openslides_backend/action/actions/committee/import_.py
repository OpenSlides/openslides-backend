from typing import Any, Dict, List

from ....models.models import ActionWorker
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.schema import required_id_schema
from ....shared.util import ONE_ORGANIZATION_ID
from ...mixins.import_mixins import ImportMixin, ImportState, Lookup
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import CommitteeCreate
from .update import CommitteeUpdateAction


@register_action("committee.import")
class CommitteeImport(ImportMixin):
    """
    Action to import committee from action worker.
    Second action of committee import feature. (See json_upload for the first.)
    """

    model = ActionWorker()
    schema = DefaultSchema(ActionWorker()).get_default_schema(
        additional_required_fields={
            "id": required_id_schema,
            "import": {"type": "boolean"},
        }
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True
    import_name = "committee"

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)

        # handle abort in on_success
        if not instance["import"]:
            return {}

        data = self.result.get("rows", [])

        # initialize the lookups
        committee_lookup = Lookup(
            self.datastore, "committee", [entry["data"]["name"] for entry in data]
        )

        # collect the payloads
        create_committee_payload: List[Dict[str, Any]] = []
        update_committee_payload: List[Dict[str, Any]] = []
        self.error = False
        for entry in data:
            if entry["state"] == ImportState.NEW:
                new_committee = self.get_committee_data_from_entry(entry)
                new_committee["organization_id"] = ONE_ORGANIZATION_ID
                if committee_lookup.check_duplicate(new_committee["name"]):
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Want to create new committee, but name exists."
                    )
                    self.error = True
                else:
                    create_committee_payload.append(new_committee)
            elif entry["state"] == ImportState.DONE:
                edit_committee = self.get_committee_data_from_entry(entry)
                if not committee_lookup.check_duplicate(edit_committee["name"]):
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Want to update committee, but could not find it."
                    )
                    self.error = True
                elif edit_committee["id"] != committee_lookup.get_id_by_name(
                    edit_committee["name"]
                ):
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Want to update committee, but id mismatches."
                    )
                    self.error = True
                else:
                    del edit_committee["name"]
                    update_committee_payload.append(edit_committee)
            elif entry["state"] == ImportState.ERROR:
                self.error = True

        # execute the actions
        if not self.error:
            if create_committee_payload:
                self.execute_other_action(CommitteeCreate, create_committee_payload)
            if update_committee_payload:
                self.execute_other_action(
                    CommitteeUpdateAction, update_committee_payload
                )
        else:
            self.error_store_ids.append(instance["id"])
        return {}

    def get_committee_data_from_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        return {
            field: entry["data"][field]
            for field in ("name", "description", "id")
            if field in entry["data"]
        }
