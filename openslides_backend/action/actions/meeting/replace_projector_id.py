from typing import List, cast

from openslides_backend.models.models import Meeting

from ....shared.patterns import FullQualifiedId
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
            fields = [
                "default_projector_${}_id".format(replacement)
                for replacement in cast(
                    List[str], Meeting.default_projector__id.replacement_enum
                )
            ]
            meeting = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]),
                fields + ["reference_projector_id"],
            )
            changed = False
            for field in fields:
                if meeting.get(field) == projector_id:
                    instance[field] = meeting["reference_projector_id"]
                    changed = True
            if changed:
                yield instance
