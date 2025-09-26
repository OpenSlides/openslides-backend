from typing import Any

from ....models.models import Committee
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
)
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .committee_common_mixin import CommitteeCommonCreateUpdateMixin
from .functions import detect_circles


@register_action("committee.update")
class CommitteeUpdateAction(CommitteeCommonCreateUpdateMixin, UpdateAction):
    """
    Action to update a committee.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_update_schema(
        optional_properties=[
            "name",
            "description",
            "default_meeting_id",
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
            "forward_agenda_to_committee_ids",
            "receive_agenda_forwardings_from_committee_ids",
            "organization_tag_ids",
            "manager_ids",
            "external_id",
            "parent_id",
        ],
    )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = list(super().get_updated_instances(action_data))
        if action_data:
            instances: dict[int, dict[str, Any]] = {
                instance["id"]: instance for instance in action_data
            }
            parent_change_ids: list[int] = list(
                {
                    id_
                    for inst in action_data
                    for id_ in (
                        [inst["id"], inst["parent_id"]]
                        if inst.get("parent_id")
                        else [inst["id"]]
                    )
                    if "parent_id" in inst
                }
            )
            if parent_change_ids:
                db_instances = self.datastore.get_many(
                    [
                        GetManyRequest(
                            "committee",
                            parent_change_ids,
                            [
                                "id",
                                "parent_id",
                                "child_ids",
                                "all_parent_ids",
                                "all_child_ids",
                            ],
                        )
                    ]
                )["committee"]
                all_other_ids = {
                    id_
                    for db_inst in db_instances.values()
                    for id_ in [
                        *db_inst.get("all_child_ids", []),
                        *db_inst.get("all_parent_ids", []),
                    ]
                }
                all_other_ids.difference_update(db_instances)
                if all_other_ids:
                    db_instances.update(
                        self.datastore.get_many(
                            [
                                GetManyRequest(
                                    "committee",
                                    list(all_other_ids),
                                    ["parent_id", "child_ids"],
                                )
                            ]
                        )["committee"]
                    )
                relevant_tree: dict[int, tuple[int | None, list[int]]] = (
                    {}
                )  # id -> parent_id, child_ids
                for id_, db_inst in db_instances.items():
                    if (inst := instances.get(id_)) and "parent_id" in inst:
                        relevant_tree[id_] = (inst["parent_id"], [])
                    else:
                        relevant_tree[id_] = (db_inst.get("parent_id"), [])
                # circle detection
                if circles := detect_circles(set(db_instances), relevant_tree):
                    raise ActionException(
                        f"Cannot perform parent updates, as it would create circles for the following committees: {circles}"
                    )
                # all_parent_ids generation
                nodes: list[tuple[int, list[int], bool]] = [
                    (id_, [], id_ in instances)
                    for id_, data in relevant_tree.items()
                    if data[0] is None
                ]
                ind = 0
                while ind < len(nodes):
                    id_, all_parent_ids, should_write = nodes[ind]
                    if should_write:
                        if id_ not in instances:
                            instances[id_] = {
                                "id": id_,
                                "all_parent_ids": all_parent_ids,
                            }
                        else:
                            instances[id_]["all_parent_ids"] = all_parent_ids
                    all_parent_ids = [*all_parent_ids, id_]
                    nodes.extend(
                        (
                            child_id,
                            all_parent_ids,
                            should_write or child_id in instances,
                        )
                        for child_id in relevant_tree[id_][1]
                    )
                    ind += 1
            action_data = list(instances.values())
        return action_data

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        if instance.get("default_meeting_id"):
            self.check_meeting_in_committee(
                instance["default_meeting_id"], instance["id"]
            )
        return instance

    def check_meeting_in_committee(self, meeting_id: int, committee_id: int) -> None:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["committee_id"],
            lock_result=False,
        )
        if meeting.get("committee_id") != committee_id:
            raise ActionException(
                f"Meeting {meeting_id} does not belong to committee {committee_id}"
            )

    def check_permissions(self, instance: dict[str, Any]) -> None:
        self.check_forwarding_fields(instance)
        if has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            return

        if "parent_id" in instance:
            if not instance["parent_id"]:
                raise MissingPermission(
                    OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                )

            child_id = instance["id"]
            parent_id = instance["parent_id"]
            data = self.datastore.get_many(
                [
                    GetManyRequest(
                        "committee",
                        [parent_id, child_id],
                        ["all_parent_ids"],
                    ),
                    GetManyRequest(
                        "user", [self.user_id], ["committee_management_ids"]
                    ),
                ],
                lock_result=False,
            )
            parent_intersection = set(
                data["committee"][child_id].get("all_parent_ids", [])
            ).intersection(
                [*data["committee"][parent_id].get("all_parent_ids", []), parent_id]
            )
            if not len(parent_intersection):
                raise MissingPermission(
                    OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                )
            permitted_ids = set(
                data["user"][self.user_id].get("committee_management_ids", [])
            ).intersection(parent_intersection)
            if not len(permitted_ids):
                raise MissingPermission(
                    {
                        OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION: 1,
                        CommitteeManagementLevel.CAN_MANAGE: parent_intersection,
                    }
                )

        if has_committee_management_level(
            self.datastore,
            self.user_id,
            instance["id"],
        ):
            return

        raise MissingPermission(
            {
                OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION: 1,
                CommitteeManagementLevel.CAN_MANAGE: instance["id"],
            }
        )
