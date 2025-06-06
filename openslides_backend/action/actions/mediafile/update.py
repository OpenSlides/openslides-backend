from typing import Any

from ....models.models import Mediafile, MeetingMediafile
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...mixins.meeting_mediafile_helper import find_meeting_mediafile
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..meeting_mediafile.create import MeetingMediafileCreate
from ..meeting_mediafile.update import MeetingMediafileUpdate
from .calculate_mixins import (
    MediafileCalculatedFieldsMixin,
    calculate_inherited_groups_helper_with_parent_id,
)
from .mixins import MediafileMixin


@register_action("mediafile.update")
class MediafileUpdate(MediafileMixin, UpdateAction, MediafileCalculatedFieldsMixin):
    """
    Action to update a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_update_schema(
        optional_properties=["title", "token"],
        additional_optional_fields={
            "meeting_id": required_id_schema,
            "access_group_ids": MeetingMediafile.access_group_ids.get_schema(),
        },
    )
    permission = Permissions.Mediafile.CAN_MANAGE

    def get_updated_instances(self, instances: ActionData) -> ActionData:
        """
        Calculate access_group_ids and inherited_access_group_ids, if
        access_group_ids and meeting_id are given.
        """
        for instance in instances:
            if instance.get("access_group_ids") is None:
                yield instance
                continue
            if meeting_id := instance.get("meeting_id"):
                mediafile = self.datastore.get(
                    fqid_from_collection_and_id(self.model.collection, instance["id"]),
                    ["parent_id"],
                )
                (
                    instance["is_public"],
                    instance["inherited_access_group_ids"],
                ) = calculate_inherited_groups_helper_with_parent_id(
                    self.datastore,
                    instance.get("access_group_ids"),
                    mediafile.get("parent_id"),
                    meeting_id,
                )
                yield instance

                # Handle children
                yield from self.handle_children(
                    instance,
                    instance["is_public"],
                    instance["inherited_access_group_ids"],
                )
            else:
                raise ActionException("Cannot update access groups without meeting_id")

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        if meeting_id := instance.pop("meeting_id", None):
            m_mediafile: dict[str, Any] = {}
            for field in [
                "is_public",
                "access_group_ids",
                "inherited_access_group_ids",
            ]:
                if field in instance:
                    m_mediafile[field] = instance.pop(field)
            if len(m_mediafile):
                m_id, _ = find_meeting_mediafile(
                    self.datastore, meeting_id, instance["id"], lock_result=False
                )
                if m_id:
                    self.execute_other_action(
                        MeetingMediafileUpdate, [{"id": m_id, **m_mediafile}]
                    )
                else:
                    if m_mediafile.get("access_group_ids") or m_mediafile.get(
                        "inherited_access_group_ids"
                    ) != [
                        self.datastore.get(
                            fqid_from_collection_and_id("meeting", meeting_id),
                            ["admin_group_id"],
                            lock_result=False,
                        )["admin_group_id"]
                    ]:
                        self.execute_other_action(
                            MeetingMediafileCreate,
                            [
                                {
                                    "meeting_id": meeting_id,
                                    "mediafile_id": instance["id"],
                                    **m_mediafile,
                                }
                            ],
                        )
        return instance
