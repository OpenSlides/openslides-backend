from openslides_backend.models.models import Meeting

from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import GetMeetingIdFromIdMixin


@register_action(
    "meeting.replace_projector_id", action_type=ActionType.BACKEND_INTERNAL
)
class MeetingReplaceProjectorId(UpdateAction, GetMeetingIdFromIdMixin):
    """
    Internal action to replace default projector id with reference id.
    """

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema(
        additional_optional_fields={"projector_id": required_id_schema}
    )

    def get_updated_instances(self, payload: ActionData) -> ActionData:
        for instance in payload:
            projector_id = instance.pop("projector_id")
            fields = Meeting.all_default_projectors()
            meeting = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                fields + ["reference_projector_id"],
            )
            changed = False
            for field in fields:
                change_list = meeting.get(field)
                if change_list and projector_id in change_list:
                    change_list.remove(projector_id)
                    if not change_list:
                        change_list.append(meeting["reference_projector_id"])
                    instance[field] = change_list
                    changed = True
            if changed:
                yield instance
