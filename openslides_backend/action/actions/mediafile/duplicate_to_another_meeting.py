import re
from time import time
from typing import Any

from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....services.database.commands import GetManyRequest
from ....shared.filters import And, FilterOperator
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
        self.ensure_unique_title_within_parent(instance)
        instance["create_timestamp"] = round(time())
        if not instance.get("is_directory"):
            self.media.duplicate_mediafile(origin_id, instance["id"])
        return instance

    def ensure_unique_title_within_parent(self, instance: dict[str, Any]) -> None:
        """
        If mediafile with the same title exists in the same directory,
        makes the title unique by adding a suffix.
        """
        title: str | None = instance.get("title")
        parent_id: int | None = instance.get("parent_id")
        owner_id: str = instance.get("owner_id", "")

        if title:
            filter_ = And(
                FilterOperator("title", "=", title),
                FilterOperator("parent_id", "=", parent_id),
                FilterOperator("owner_id", "=", owner_id),
            )
            results = self.datastore.filter(self.model.collection, filter_, ["id"])

            if results:
                instance["title"] = self.get_title_with_unique_suffix(
                    title, owner_id, parent_id
                )

    def get_title_with_unique_suffix(
        self,
        origin_title: str,
        owner_id: str,
        parent_id: int | None,
    ) -> str:
        """
        Scans for existing titles within the same folder (by `parent_id`) or root
        (if None), matching 'base_title' or 'base_title (#n)'.
        Returns a unique title like 'base_title (#n)'.
        If only 'base_title' is present, returns 'base_title (#2)'.
        """
        filter_ = And(
            FilterOperator("owner_id", "=", owner_id),
            FilterOperator("parent_id", "=", parent_id),
        )
        existing_titles = {
            item.get("title", "")
            for item in self.datastore.filter(
                self.model.collection, filter_, ["title"]
            ).values()
        }

        pattern = re.compile(rf"^{re.escape(origin_title)}(?:\s\(#(\d+)\))?$")
        max_suffix = 1

        for title in existing_titles:
            match = pattern.match(title)
            if match:
                suffix_str = match.group(1)
                if suffix_str:
                    try:
                        suffix_num = int(suffix_str)
                        max_suffix = max(max_suffix, suffix_num)
                    except ValueError:
                        continue

        return f"{origin_title} (#{max_suffix + 1})"
