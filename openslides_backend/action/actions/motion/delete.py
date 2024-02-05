from typing import Any

from openslides_backend.action.action import merge_history_informations
from openslides_backend.shared.typing import HistoryInformation

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
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
