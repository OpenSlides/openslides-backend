from typing import Any, cast

from ...action import Action, ActionResults
from ...mixins.meeting_mediafile_helper import (
    get_meeting_mediafile_id_or_create_payload,
)
from .create import MeetingMediafileCreate


class AttachmentMixin(Action):
    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        if "attachment_mediafile_ids" in instance:
            attachment_ids = instance.pop("attachment_mediafile_ids", [])
            meeting_id = self.get_meeting_id(instance)
            attachment_data = [
                get_meeting_mediafile_id_or_create_payload(
                    self.datastore, meeting_id, attachment_id, lock_result=False
                )
                for attachment_id in attachment_ids
            ]
            result_ids: list[int] = [
                cast(dict[str, Any], result)["id"]
                for result in cast(
                    ActionResults,
                    self.execute_other_action(
                        MeetingMediafileCreate,
                        [
                            attachement
                            for attachement in attachment_data
                            if not isinstance(attachement, int)
                        ],
                    ),
                )
            ]
            j = 0
            for i in range(len(attachment_data)):
                if not isinstance(attachment_data[i], int):
                    attachment_data[i] = result_ids[j]
                    j += 1
            instance["attachment_meeting_mediafile_ids"] = attachment_data
        return instance
