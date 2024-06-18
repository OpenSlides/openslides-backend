from collections.abc import Iterable
from typing import Any

from openslides_backend.action.action import merge_history_informations
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import MissingPermission
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import PermissionHelperMixin


@register_action("motion.delete")
class MotionDelete(DeleteAction, PermissionHelperMixin):
    """
    Action to delete motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_delete_schema()
    history_information = "Motion deleted"
    all_motion_ids: list[int]

    def check_permissions(self, instance: dict[str, Any]) -> None:
        motion = self.datastore.get(
            fqid_from_collection_and_id("motion", instance["id"]),
            [
                "state_id",
                "submitter_ids",
                "meeting_id",
            ],
            lock_result=False,
        )
        if has_perm(
            self.datastore,
            self.user_id,
            Permissions.Motion.CAN_MANAGE,
            motion["meeting_id"],
        ):
            return

        if self.is_allowed_and_submitter(
            motion.get("submitter_ids", []),
            motion["state_id"],
        ):
            return

        raise MissingPermission(Permissions.Motion.CAN_MANAGE)

    def get_updated_instances(
        self, action_data: Iterable[dict[str, Any]]
    ) -> Iterable[dict[str, Any]]:
        # remove amendments of other deleted motions as they will be cascaded
        instances = list(super().get_updated_instances(action_data))
        self.all_motion_ids = [item["id"] for item in instances]
        motions = self.datastore.get_many(
            [GetManyRequest("motion", self.all_motion_ids, ["lead_motion_id"])]
        )["motion"]
        instances = [
            instance
            for instance in instances
            if not (
                motions[instance["id"]].get("lead_motion_id") in self.all_motion_ids
            )
        ]
        return instances

    def get_history_information(self) -> HistoryInformation | None:
        information = super().get_history_information()
        if self.history_information is None:
            return information
        # generate the history informations for the deleted amendments
        fqids = [
            fqid_from_collection_and_id("motion", id_) for id_ in self.all_motion_ids
        ]
        if not information:
            information = {fqid: [self.history_information] for fqid in fqids}
        else:
            for fqid in fqids:
                information[fqid] = [self.history_information]
        return information

    def get_full_history_information(self) -> HistoryInformation | None:
        """
        Discard history informations from cascaded delete actions.
        """
        information = self.get_history_information()
        instances = self.get_instances_with_fields(
            ["all_origin_ids", "all_derived_motion_ids"]
        )
        return merge_history_informations(
            information or {},
            {
                fqid_from_collection_and_id("motion", id): ["Forwarded motion deleted"]
                for instance in instances
                for id in instance.get("all_origin_ids", [])
            },
            {
                fqid_from_collection_and_id("motion", id): ["Origin motion deleted"]
                for instance in instances
                for id in instance.get("all_derived_motion_ids", [])
            },
        )
