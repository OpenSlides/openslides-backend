from typing import Any

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import Mediafile
from ....permissions.management_levels import OrganizationManagementLevel
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import KEYSEPARATOR, fqid_from_collection_and_id
from ....shared.util import ONE_ORGANIZATION_ID
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..meeting_mediafile.delete import MeetingMediafileDelete


@register_action("mediafile.publish")
class MediafilePublish(UpdateAction, CheckForArchivedMeetingMixin):
    """
    Action to publish or un-publish a mediafile on the orga level.
    Un-publishing will delete all meeting-mediafiles of the un-published models
    and those of their children that are not published in another way.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_update_schema(
        required_properties=["is_published_to_meetings"],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        relation_key = "published_to_meetings_in_organization_id"
        for instance in action_data:
            mediafile = self.datastore.get(
                fqid_from_collection_and_id("mediafile", instance["id"]),
                [
                    "owner_id",
                    "child_ids",
                    "parent_id",
                    relation_key,
                    "is_published_to_meetings",
                    "meeting_mediafile_ids",
                ],
            )
            instance["meeting_mediafile_ids"] = mediafile.get("meeting_mediafile_ids")
            collection, _ = str(mediafile["owner_id"]).split(KEYSEPARATOR)
            if collection != "organization":
                raise ActionException(
                    "Only organization-owned mediafiles may be published"
                )
            if instance["is_published_to_meetings"] == mediafile.get(
                "is_published_to_meetings", False
            ):
                yield instance
            if parent_id := mediafile.get("parent_id"):
                parent = self.datastore.get(
                    fqid_from_collection_and_id("mediafile", parent_id), [relation_key]
                )
                if parent.get(relation_key):
                    # if the parent is visible, this mediafile and all its children
                    # are already visible and can remain so
                    yield instance
                    continue
            yield from self.get_publish_instances(
                instance,
                instance["is_published_to_meetings"],
                mediafile.get("child_ids", []),
            )

    def get_publish_instances(
        self, instance: dict[str, Any], is_published: bool, child_ids: list[int]
    ) -> ActionData:
        instance["published_to_meetings_in_organization_id"] = (
            ONE_ORGANIZATION_ID if is_published else None
        )
        yield instance
        if len(child_ids):
            children = self.datastore.get_many(
                [
                    GetManyRequest(
                        "mediafile",
                        child_ids,
                        [
                            "child_ids",
                            "is_published_to_meetings",
                            "meeting_mediafile_ids",
                        ],
                    )
                ]
            )["mediafile"]
            for id_, child in children.items():
                if not child.get("is_published_to_meetings"):
                    yield from self.get_publish_instances(
                        {
                            "id": id_,
                            "meeting_mediafile_ids": child.get("meeting_mediafile_ids"),
                        },
                        is_published,
                        child.get("child_ids", []),
                    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        if (
            (meeting_mediafile_ids := instance.pop("meeting_mediafile_ids", None))
            and "published_to_meetings_in_organization_id" in instance
            and instance.get("published_to_meetings_in_organization_id") is None
        ):
            self.execute_other_action(
                MeetingMediafileDelete, [{"id": id_} for id_ in meeting_mediafile_ids]
            )
        return instance
