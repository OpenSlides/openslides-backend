from time import time
from typing import Any

from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import fqid_from_collection_and_id
from ...generics.create import CreateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import MediafileCreateMixin

FIELDS = [
    "title",
    "is_directory",
    "filesize",
    "filename",
    "mimetype",
    "pdf_information",
]
#


@register_action(
    "mediafile.duplicate_to_another_meeting", action_type=ActionType.BACKEND_INTERNAL
)
class MediafileDuplicateToAnotherMeetingAction(MediafileCreateMixin, CreateAction):
    """
    Action to duplicate an existing mediafile to another meeting.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_create_schema(
        required_properties=["id", "owner_id"],
        optional_properties=["parent_id"],
        additional_required_fields={
            "origin_id": {"type": "integer"},
        },
    )
    permission = Permissions.Mediafile.CAN_MANAGE

    def prepare_action_data(self, action_data: ActionData) -> ActionData:
        return action_data

    def prefetch(self, action_data: ActionData) -> None:
        self.datastore.get_many(
            [
                GetManyRequest(
                    "mediafile",
                    list({instance["origin_id"] for instance in action_data}),
                    FIELDS,
                ),
            ],
            use_changed_models=False,
        )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        origin_id = instance.pop("origin_id")
        instance.update(
            self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, origin_id),
                FIELDS,
                lock_result=False,
            )
        )
        instance["create_timestamp"] = round(time())
        if not instance.get("is_directory"):
            self.media.duplicate_mediafile(origin_id, instance["id"])
        return instance
