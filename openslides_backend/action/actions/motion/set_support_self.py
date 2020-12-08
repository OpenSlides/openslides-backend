from ....models.models import Motion
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionPayload


@register_action("motion.set_support_self")
class MotionSetSupportSelfAction(UpdateAction):
    """
    Action to add the user to the support of a motion.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_default_schema(
        title="Schema for set support self",
        description="motion_id is a required id and support is a boolean.",
        additional_required_fields={
            "motion_id": required_id_schema,
            "support": {"type": "boolean"},
        },
    )

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        for instance in payload:
            motion = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["motion_id"]),
                ["meeting_id", "state_id", "supporter_ids"],
            )
            if not motion.get("meeting_id"):
                raise ActionException("Motion is missing meeting_id.")
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), motion["meeting_id"]),
                ["motions_supporters_min_amount"],
            )
            if meeting.get("motions_supporters_min_amount") == 0:
                raise ActionException("Motion supporters system deactivated.")
            if not motion.get("state_id"):
                raise ActionException("Motion is missing state_id.")
            state = self.datastore.get(
                FullQualifiedId(Collection("motion_state"), motion["state_id"]),
                ["allow_support"],
            )
            if state.get("allow_support") is False:
                raise ActionException("The state does not allow support.")

            supporter_ids = motion.get("supporter_ids", [])
            changed = False
            motion_id = instance.pop("motion_id")
            support = instance.pop("support")

            if support:
                if self.user_id not in supporter_ids:
                    supporter_ids.append(self.user_id)
                    changed = True
            else:
                if self.user_id in supporter_ids:
                    supporter_ids.remove(self.user_id)
                    changed = True
            instance["id"] = motion_id
            if changed:
                instance["supporter_ids"] = supporter_ids
                yield instance
