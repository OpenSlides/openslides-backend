
from ....models.models import Meeting
from ....shared.patterns import FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import GetMeetingIdFromIdMixin
from .shared_meeting import meeting_projector_default_replacements


@register_action("meeting.replace_projector_id", internal=True)
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
                for replacement in meeting_projector_default_replacements
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
