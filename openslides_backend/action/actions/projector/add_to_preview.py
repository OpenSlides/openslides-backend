from typing import Any, cast

from ....models.models import Projection, Projector
from ....permissions.permissions import Permissions
from ....shared.filters import And, FilterOperator
from ....shared.patterns import collection_and_id_from_fqid, fqid_from_collection_and_id
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...mixins.meeting_mediafile_helper import (
    get_meeting_mediafile_id_or_create_payload,
)
from ...mixins.weight_mixin import WeightMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..meeting_mediafile.create import MeetingMediafileCreate
from ..projection.create import ProjectionCreate


@register_action("projector.add_to_preview")
class ProjectorAddToPreview(WeightMixin, UpdateAction):
    """
    Action to projector project.
    """

    model = Projector()
    schema = DefaultSchema(Projection()).get_default_schema(
        required_properties=["content_object_id", "meeting_id"],
        optional_properties=["options", "stable", "type"],
        additional_required_fields={"ids": id_list_schema},
        title="Projector add to preview schema",
    )
    permission = Permissions.Projector.CAN_MANAGE

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            meeting_id = instance["meeting_id"]
            fqid_content_object = instance["content_object_id"]
            content_object_collection, content_object_id = collection_and_id_from_fqid(
                fqid_content_object
            )
            if content_object_collection == "mediafile":
                meeting_mediafile = get_meeting_mediafile_id_or_create_payload(
                    self.datastore, meeting_id, content_object_id, lock_result=False
                )
                if not isinstance(meeting_mediafile, int):
                    create_result = self.execute_other_action(
                        MeetingMediafileCreate, [meeting_mediafile]
                    )
                    meeting_mediafile_id: int = cast(
                        list[dict[str, Any]], create_result
                    )[0]["id"]
                else:
                    meeting_mediafile_id = meeting_mediafile
                fqid_content_object = instance["content_object_id"] = (
                    fqid_from_collection_and_id(
                        "meeting_mediafile", meeting_mediafile_id
                    )
                )
            # add the preview projections
            for projector_id in instance["ids"]:
                filter = And(
                    FilterOperator("preview_projector_id", "=", projector_id),
                    FilterOperator("meeting_id", "=", instance["meeting_id"]),
                )
                weight = self.get_weight(filter, "projection")
                data = {
                    "meeting_id": meeting_id,
                    "preview_projector_id": projector_id,
                    "weight": weight,
                    "content_object_id": instance["content_object_id"],
                }
                for field in ("options", "stable", "type"):
                    if instance.get(field):
                        data[field] = instance[field]
                self.execute_other_action(ProjectionCreate, [data])
        return []
