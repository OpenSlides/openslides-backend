from typing import Any

import fastjsonschema  # type: ignore

from ...models.topic import Topic
from ...shared.exceptions import PermissionDenied
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedField, FullQualifiedId
from ...shared.permissions.topic import TOPIC_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..actions_interface import Payload
from ..base import Action, DataSet

create_topic_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "New topics schema",
        "description": "An array of new topics.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "meeting_id": Topic().get_schema("meeting_id"),
                "title": Topic().get_schema("title"),
                "text": Topic().get_schema("text"),
                "mediafile_attachment_ids": Topic().get_schema(
                    "mediafile_attachment_ids"
                ),
            },
            "required": ["meeting_id", "title"],
        },
        "minItems": 1,
        "uniqueItems": False,
    }
)


@register_action("topic.create")
class TopicCreate(Action):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = create_topic_schema

    def check_permission(self, meeting_id: int) -> None:
        required_permission = f"{meeting_id}/{TOPIC_CAN_MANAGE}"
        if not self.permission.has_perm(self.user_id, required_permission):
            raise PermissionDenied(
                f"User does not have {TOPIC_CAN_MANAGE} permission for meeting {meeting_id}."
            )

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for topic in payload:
            self.check_permission(topic["meeting_id"])
            id, position = self.database.getId(collection=self.model.collection)
            self.set_min_position(position)
            references = self.get_references(
                model=self.model,
                id=id,
                obj=topic,
                fields=["meeting_id", "mediafile_attachment_ids"],
            )
            data.append({"topic": topic, "new_id": id, "references": references})
        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        fqfields = {}

        # Title
        fqfields[
            FullQualifiedField(self.model.collection, element["new_id"], "title")
        ] = element["topic"]["title"]

        # Text
        text = element["topic"].get("text")
        if text is not None:
            fqfields[
                FullQualifiedField(self.model.collection, element["new_id"], "text")
            ] = text

        # Mediafile attachments
        mediafile_attachment_ids = element["topic"].get("mediafile_attachment_ids")
        if mediafile_attachment_ids:
            fqfields[
                FullQualifiedField(
                    self.model.collection, element["new_id"], "mediafile_attachment_ids"
                )
            ] = mediafile_attachment_ids

        information = {
            FullQualifiedId(self.model.collection, element["new_id"]): ["Topic created"]
        }
        event = Event(type="create", fqfields=fqfields)
        return WriteRequestElement(
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={},
        )
