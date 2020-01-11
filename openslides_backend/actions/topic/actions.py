from typing import Any, Iterable

from fastjsonschema import JsonSchemaException  # type: ignore

from ...adapters.protocols import Event
from ...general.patterns import Collection, FullQualifiedField
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
        if not self.permission_adapter.has_perm(self.user_id, "topic.can_manage"):
            raise PermissionDenied("User does not have topic.can_manage permission.")

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
            if topic.get("mediafile_attachment_ids"):
                mediafile_attachment, position = self.database_adapter.getMany(
                    collection=Collection("mediafile_attachment"),
                    ids=topic["mediafile_attachment_ids"],
                    mapped_fields=["topic_ids"],
                )
                self.set_min_position(position)
            else:
                mediafile_attachment = {}
            data.append(
                {
                    "topic": topic,
                    "new_id": id,
                    "mediafile_attachment": mediafile_attachment,
                }
            )
        return {"position": self.position, "data": data}

    def create_events(self, dataset: DataSet) -> Iterable[Event]:
        position = dataset["position"]
        for element in dataset["data"]:
            yield self.create_topic_event(position, element)
            for mediafile_attachment_id in element["topic"].get(
                "mediafile_attachment_ids", []
            ):
                information = {
                    "user_id": self.user_id,
                    "text": "Mediafile attached to new topic.",
                }
                fields = {}

                # Topic Ids
                topic_ids = element["mediafile_attachment"][mediafile_attachment_id][
                    "topic_ids"
                ] + [element["new_id"]]
                fields[
                    FullQualifiedField(
                        Collection("mediafile_attachment"),
                        mediafile_attachment_id,
                        "topic_ids",
                    )
                ] = topic_ids

                yield Event(
                    type="update",
                    position=position,
                    information=information,
                    fields=fields,
                )

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
