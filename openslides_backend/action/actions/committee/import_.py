from typing import Any, Callable, Dict, List, Set, Type, cast

from ....models.models import ActionWorker
from ....permissions.management_levels import OrganizationManagementLevel
from ....shared.schema import required_id_schema
from ....shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from ...action import Action
from ...mixins.import_mixins import ImportMixin, ImportState, Lookup, ResultType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..meeting.clone import MeetingClone
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
            self.datastore,
            "committee",
            [entry["data"]["name"]["value"] for entry in data],
        )

        # collect the payloads
        create_committee_payload: List[Dict[str, Any]] = []
        update_committee_payload: List[Dict[str, Any]] = []
        self.error = False
        if any(entry["data"].get("organization_tags") for entry in data):

            def get_ot_create_payload(name: str) -> Dict[str, Any]:
                return {
                    "name": name,
                    "organization_id": ONE_ORGANIZATION_ID,
                    "color": "#ffffff",
                }

            self.handle_list_field(
                "organization_tags",
                "organization_tag_ids",
                data,
                OrganizationTagCreate,
                get_ot_create_payload,
            )
        if any(entry["data"].get("forward_to_committees") for entry in data):

            def get_fc_create_payload(name: str) -> Dict[str, Any]:
                return {
                    "name": name,
                    "organization_id": ONE_ORGANIZATION_ID,
                }

            self.handle_list_field(
                "forward_to_committees",
                "forward_to_committee_ids",
                data,
                CommitteeCreate,
                get_fc_create_payload,
            )

        for entry in data:
            self.handle_committee_managers(entry)
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
                        e["data"]["name"]["value"]: e["data"]["name"]["id"]
                        for e in data
                        if e["state"] == ImportState.DONE
                    }
                )
        else:
            self.error_store_ids.append(instance["id"])

        # create meetings
        if any(entry["data"].get("meeting_name") for entry in data):
            create_meeting_payload: List[Dict[str, Any]] = []
            clone_meeting_payload: List[Dict[str, Any]] = []
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
                    pl["committee_id"] = change_committees[
                        entry["data"]["name"]["value"]
                    ]
                    if entry["data"].get("meeting_admins"):
                        pl["admin_ids"] = [
                            inner["id"]
                            for inner in entry["data"]["meeting_admins"]
                            if inner.get("id")
                        ]
                    if (
                        meeting_id := entry["data"]
                        .get("meeting_template", {})
                        .get("id")
                    ):
                        pl["meeting_id"] = meeting_id
                        del pl["language"]
                        clone_meeting_payload.append(pl)
                    else:
                        create_meeting_payload.append(pl)
            if clone_meeting_payload:
                self.execute_other_action(MeetingClone, clone_meeting_payload)
            if create_meeting_payload:
                self.execute_other_action(MeetingCreate, create_meeting_payload)
        return {}

    def get_committee_data_from_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            field: entry["data"][field]
            for field in (
                "description",
                "organization_tag_ids",
                "manager_ids",
                "forward_to_committee_ids",
            )
            if field in entry["data"]
        }
        result["name"] = entry["data"]["name"]["value"]
        if entry["data"]["name"].get("id"):
            result["id"] = entry["data"]["name"]["id"]
        return result

    def handle_list_field(
        self,
        data_name: str,
        payload_name: str,
        data: List[Dict[str, Any]],
        create_action: Type[Action],
        get_create_payload: Callable[[str], Dict[str, Any]],
    ) -> None:
        create_names: Set[str] = set()
        name_to_id: Dict[str, int] = {}
        for entry in data:
            for innerentry in entry["data"].get(data_name, []):
                if innerentry["info"] == ImportState.WARNING:
                    pass
                elif not innerentry.get("id"):
                    create_names.add(cast(str, innerentry["value"]))
                else:
                    name_to_id[innerentry["value"]] = innerentry["id"]
        # create payload and execute create action
        created_names: List[str] = list(create_names)
        create_payload = [get_create_payload(name) for name in created_names]
        create_results = self.execute_other_action(create_action, create_payload)
        created_ids = [(r or {})["id"] for r in (create_results or [])]
        for name, id_ in zip(created_names, created_ids):
            name_to_id[name] = id_
        # set the payload name
        for entry in data:
            if entry["data"].get(data_name):
                collect_ids: List[int] = []
                for innerentry in entry["data"][data_name]:
                    if innerentry["info"] == ImportState.WARNING:
                        continue
                    id_ = name_to_id[innerentry["value"]]
                    if id_ not in collect_ids:
                        collect_ids.append(id_)
                entry["data"][payload_name] = collect_ids

    def handle_committee_managers(self, entry: Dict[str, Any]) -> None:
        if "committee_managers" in entry["data"]:
            entry["data"]["manager_ids"] = [
                inner["id"]
                for inner in entry["data"].get("committee_managers", [])
                if inner.get("id")
            ]
