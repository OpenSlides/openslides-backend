from typing import Any, Dict, List, Set, cast

from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from ...mixins.import_mixins import ImportMixin, ImportState, Lookup, ResultType
from ...util.register import register_action
from ..meeting.create import MeetingCreate
from ..organization_tag.create import OrganizationTagCreate
from .create import CommitteeCreate
from .update import CommitteeUpdateAction


@register_action("committee.import")
class CommitteeImport(ImportMixin):
    """
    Action to import committee from action worker.
    Second action of committee import feature. (See json_upload for the first.)
    """

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
        if any(entry["data"].get("organization_tags") for entry in data):
            self.handle_organization_tags(data)
        for entry in data:
            if entry["state"] == ImportState.NEW:
                new_committee = self.get_committee_data_from_entry(entry)
                new_committee["organization_id"] = ONE_ORGANIZATION_ID
                if (
                    committee_lookup.check_duplicate(new_committee["name"])
                    != ResultType.NOT_FOUND
                ):
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Want to create new committee, but name exists."
                    )
                    self.error = True
                else:
                    create_committee_payload.append(new_committee)
            elif entry["state"] == ImportState.DONE:
                edit_committee = self.get_committee_data_from_entry(entry)
                result_type = committee_lookup.check_duplicate(edit_committee["name"])
                if result_type == ResultType.NOT_FOUND:
                    entry["state"] = ImportState.ERROR
                    entry["messages"].append(
                        "Want to update committee, but could not find it."
                    )
                    self.error = True
                elif edit_committee["id"] != committee_lookup.get_field_by_name(
                    edit_committee["name"], "id"
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
            change_committees: Dict[str, int] = {}
            if create_committee_payload:
                results = self.execute_other_action(
                    CommitteeCreate, create_committee_payload
                )
                change_committees.update(
                    {
                        cr["name"]: re["id"]
                        for cr, re in zip(create_committee_payload, results or [])
                        if re
                    }
                )

            if update_committee_payload:
                self.execute_other_action(
                    CommitteeUpdateAction, update_committee_payload
                )
                change_committees.update(
                    {
                        e["data"]["name"]: e["data"]["id"]
                        for e in data
                        if e["state"] == ImportState.DONE
                    }
                )
        else:
            # self.error_store_ids.append(instance["id"])
            pass

        # create meetings
        if any(entry["data"].get("meeting_name") for entry in data):
            meeting_payload: List[Dict[str, Any]] = []
            organization = self.datastore.get(
                ONE_ORGANIZATION_FQID, ["default_language"]
            )
            for entry in data:
                if entry["data"].get("meeting_name"):
                    pl: Dict[str, Any] = {"name": entry["data"]["meeting_name"]}
                    for field in ("start_time", "end_time"):
                        if entry["data"].get(field):
                            pl[field] = entry["data"][field]
                    pl["language"] = organization.get("default_language", "en")
                    pl["committee_id"] = change_committees[entry["data"]["name"]]
                    if entry["data"].get("meeting_admins"):
                        pl["admin_ids"] = [
                            inner["id"]
                            for inner in entry["data"]["meeting_admins"]
                            if inner["info"] == ImportState.DONE
                        ]

                    meeting_payload.append(pl)
            self.execute_other_action(MeetingCreate, meeting_payload)
        return {}

    def get_committee_data_from_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        return {
            field: entry["data"][field]
            for field in ("name", "description", "id", "organization_tag_ids")
            if field in entry["data"]
        }

    def handle_organization_tags(self, data: List[Dict[str, Any]]) -> None:
        create_otnames: Set[str] = set()
        otname_to_id: Dict[str, int] = {}
        for entry in data:
            for otentry in entry["data"].get("organization_tag_ids", []):
                if otentry["info"] == ImportState.NEW:
                    create_otnames.add(cast(str, otentry["value"]))
                elif entry["info"] == ImportState.DONE:
                    otname_to_id[otentry["value"]] = otentry["id"]
        # create payload and execute create action
        created_names: List[str] = list(create_otnames)
        create_ots_payload = [
            {"name": otname, "organization_id": ONE_ORGANIZATION_ID}
            for otname in created_names
        ]
        ot_create_results = self.execute_other_action(
            OrganizationTagCreate, create_ots_payload
        )
        created_ids = [(r or {})["id"] for r in (ot_create_results or [])]
        for name, id_ in zip(created_names, created_ids):
            otname_to_id[name] = id_
        # set the organization_tag_ids
        for entry in data:
            if entry["data"].get("organization_tag_ids"):
                collect_ot_ids: List[int] = []
                for otentry in entry["data"]["organization_tags"]:
                    id_ = otname_to_id[otentry["value"]]
                    if id_ not in collect_ot_ids:
                        collect_ot_ids.append(id_)
                entry["data"]["organization_tag_ids"] = collect_ot_ids
