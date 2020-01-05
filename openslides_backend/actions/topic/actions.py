from typing import Iterable

from fastjsonschema import JsonSchemaException  # type: ignore

from ...exceptions import ActionException
from ...utils.types import Collection, Event
from ..action_map import register_action
from ..base import Action
from ..types import DataSet, Payload
from .schema import is_valid_new_topic


@register_action("topic.create")
class TopicCreate(Action):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    def validate(self, payload: Payload) -> None:
        try:
            is_valid_new_topic(payload)
        except JsonSchemaException as exception:
            raise ActionException(exception.message)

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for topic in payload:
            id, position = self.database_adapter.getId(collection=Collection("topic"))
            self.set_min_position(position)
            if topic.get("attachments"):
                mediafiles, positon = self.database_adapter.getMany(
                    collection=Collection("mediafile.attachment"),
                    ids=topic["attachments"],
                    mapped_fields=["topic_ids"],
                )
                self.set_min_position(position)
            else:
                mediafiles = []
            data.append(
                {"topic": topic, "new_id": id, "mediafile.attachment": mediafiles}
            )
        return {"position": self.position, "data": data}

    def create_events(self, dataset: DataSet) -> Iterable[Event]:
        return []
