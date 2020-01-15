from typing import Any, Iterable

from fastjsonschema import JsonSchemaException  # type: ignore

from ...adapters.protocols import Event
from ...general.patterns import Collection, FullQualifiedField
from ...models.topic import Topic
from ...permissions.topic import TOPIC_CAN_MANAGE
from ..action_map import register_action
from ..base import Action, ActionException, PermissionDenied
from ..types import DataSet, Payload
from .schema import is_valid_new_topic


@register_action("topic.create")
class TopicCreate(Action):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    collection = Collection("topic")

    def check_permission_on_entry(self) -> None:
        if not self.permission_adapter.has_perm(self.user_id, TOPIC_CAN_MANAGE):
            raise PermissionDenied(f"User does not have {TOPIC_CAN_MANAGE} permission.")

    def validate(self, payload: Payload) -> None:
        try:
            is_valid_new_topic(payload)
        except JsonSchemaException as exception:
            raise ActionException(exception.message)

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for topic in payload:
            id, position = self.database_adapter.getId(collection=self.collection)
            self.set_min_position(position)
            references = self.get_references(
                model_class=Topic,
                id=id,
                obj=topic,
                fields=["meeting_id", "mediafile_attachment_ids"],
            )
            data.append({"topic": topic, "new_id": id, "references": references})
        return {"position": self.position, "data": data}

    def create_events(self, dataset: DataSet) -> Iterable[Event]:
        position = dataset["position"]
        for element in dataset["data"]:
            yield self.create_topic_event(position, element)
            yield from self.get_references_updates(position, element)

    def create_topic_event(self, position: int, element: Any) -> Event:
        information = {"user_id": self.user_id, "text": "Topic created"}
        fields = {}

        # Title
        fields[
            FullQualifiedField(self.collection, element["new_id"], "title")
        ] = element["topic"]["title"]

        # Text
        text = element["topic"].get("text")
        if text is not None:
            fields[
                FullQualifiedField(self.collection, element["new_id"], "text")
            ] = text

        # Mediafile attachments
        mediafile_attachment_ids = element["topic"].get("mediafile_attachment_ids")
        if mediafile_attachment_ids:
            fields[
                FullQualifiedField(
                    self.collection, element["new_id"], "mediafile_attachment_ids"
                )
            ] = mediafile_attachment_ids

        return Event(
            type="create", position=position, information=information, fields=fields,
        )

    def get_references_updates(self, position: int, element: Any) -> Iterable[Event]:
        for fqfield, data in element["references"].items():
            information = {
                "user_id": self.user_id,
                "text": "Object attached to new topic",
            }
            fields = {fqfield: data}
            yield Event(
                type="update",
                position=position,
                information=information,
                fields=fields,
            )
