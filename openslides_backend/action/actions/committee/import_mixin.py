from typing import Any

from openslides_backend.shared.filters import FilterOperator

from ....services.datastore.commands import GetManyRequest
from ...action import Action
from ...mixins.import_mixins import ImportRow, ImportState
from .functions import detect_circles


class CommitteeImportMixin(Action):
    def check_admin_groups_for_meeting(self, row: dict[str, Any] | ImportRow) -> None:
        entry = row["data"]
        if entry.get("meeting_name") and not any(
            admin
            for admin in entry.get("meeting_admins", [])
            if admin.get("info") == ImportState.DONE
        ):
            admin_ids: list[int] = []
            if (
                template_id := entry.get("meeting_template", {}).get("id")
            ) and entry.get("meeting_template", {}).get("info") == ImportState.DONE:
                groups = self.datastore.filter(
                    "group",
                    FilterOperator("admin_group_for_meeting_id", "=", template_id),
                    ["meeting_user_ids"],
                )
                admin_ids = [
                    meeting_user_id
                    for group in groups.values()
                    for meeting_user_id in (group.get("meeting_user_ids") or [])
                ]
            if not len(admin_ids):
                row["state"] = ImportState.ERROR
                entry["meeting_admins"] = [
                    *entry.get("meeting_admins", []),
                    {"value": "", "info": ImportState.ERROR},
                ]
                row["messages"].append(
                    "Error: Meeting cannot be created without admins"
                )

    def check_parents_for_circles(
        self, rows: list[ImportRow] | list[dict[str, Any]]
    ) -> bool:
        """
        Searches for circles formed through the changes in the rows.
        Returns true if any error has been added.
        """
        new_relations: dict[str, str | None] = {
            row["data"]["name"]["value"]: row["data"].get("parent", {}).get("value")
            for row in rows
            if row["data"]["name"]["info"] != ImportState.ERROR
            and row["data"].get("parent")
            and row["data"].get("parent", {}).get("info") != ImportState.ERROR
        }
        has_error = False
        if len(new_relations):
            child_ids = {
                row["data"]["id"]
                for row in rows
                if "id" in row["data"]
                and row["data"]["name"]["info"] != ImportState.ERROR
                and row["data"].get("parent", {}).get("info")
                in [ImportState.NEW, ImportState.DONE]
            }
            parent_ids = {
                row["data"]["parent"]["id"]
                for row in rows
                if row["data"]["name"]["info"] != ImportState.ERROR
                and row["data"].get("parent", {}).get("info") == ImportState.DONE
            }
            parent_ids.difference_update(child_ids)
            db_instances = self.datastore.get_many(
                [
                    GetManyRequest(
                        "committee", list(child_ids), ["name", "all_child_ids"]
                    ),
                    GetManyRequest(
                        "committee",
                        list(parent_ids),
                        ["name", "parent_id", "all_parent_ids"],
                    ),
                ]
            )["committee"]
            all_other_ids = {
                id_
                for inst in db_instances.values()
                for id_ in [
                    *inst.get("all_child_ids", []),
                    *inst.get("all_parent_ids", []),
                ]
            }
            all_other_ids.difference_update(child_ids, parent_ids)
            db_instances.update(
                self.datastore.get_many(
                    [
                        GetManyRequest(
                            "committee", list(all_other_ids), ["name", "parent_id"]
                        )
                    ]
                )["committee"]
            )
            id_to_name: dict[int, str] = {
                id_: inst["name"] for id_, inst in db_instances.items()
            }
            for row in rows:
                if (name := row["data"]["name"]["value"]) in new_relations:
                    if "id" in row["data"] and (id_ := row["data"]["id"]) in id_to_name:
                        id_to_name[id_] = name
                    if (
                        "parent" in row["data"]
                        and "id" in (parent := row["data"]["parent"])
                        and (id_ := parent["id"]) in id_to_name
                    ):
                        id_to_name[id_] = parent["value"]
            for inst in db_instances.values():
                if (name := inst["name"]) not in new_relations or new_relations[
                    name
                ] is None:
                    new_relations[name] = (
                        id_to_name[parent_id]
                        if (parent_id := inst.get("parent_id"))
                        else None
                    )
            check_list: set[str] = {
                *id_to_name.values(),
                *new_relations.keys(),
                *[val for val in new_relations.values() if val],
            }
            for parent in list(new_relations.values()):
                if parent and parent not in new_relations:
                    new_relations[parent] = None
            circles = detect_circles(check_list, new_relations)
            for row in rows:
                if row["data"]["name"]["value"] in circles:
                    has_error = True
                    row["data"]["parent"] = {
                        "value": row["data"]["parent"]["value"],
                        "info": ImportState.ERROR,
                    }
                    row["state"] = ImportState.ERROR
                    row["messages"].append(
                        "Error: The parents are forming circles, please rework the hierarchy"
                    )
        return has_error
