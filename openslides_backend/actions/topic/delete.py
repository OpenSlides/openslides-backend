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

delete_topic_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Delete topics schema",
        "description": "An array of topics to be deleted.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"id": Topic().get_schema("id")},
            "required": ["id"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("topic.delete")
class TopicDelete(Action):
    """
    Action to delete simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = delete_topic_schema

    def check_permission_on_entry(self) -> None:
        if not self.permission.has_perm(self.user_id, TOPIC_CAN_MANAGE):
            raise PermissionDenied(f"User does not have {TOPIC_CAN_MANAGE} permission.")

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for topic in payload:
            exists, position = self.database.exists(
                collection=self.model.collection, ids=[topic["id"]]
            )
            self.set_min_position(position)
            topic["meeting_id"] = None
            topic["mediafile_attachment_ids"] = []
            references = self.get_references(
                model=self.model,
                id=topic["id"],
                obj=topic,
                fields=["meeting_id", "mediafile_attachment_ids"],
                deletion_possible=True,
            )
            data.append({"topic": topic, "references": references})
        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        fqid = FullQualifiedId(self.model.collection, element["topic"]["id"])
        information = {fqid: ["Topic deleted"]}
        event = Event(type="delete", fqid=fqid)
        return WriteRequestElement(
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={
                FullQualifiedField(self.model.collection, fqid.id, "deleted"): position
            },
        )
