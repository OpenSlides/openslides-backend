from typing import Iterable

from ...models.topic import Topic
from ...shared.interfaces import WriteRequestElement
from ...shared.patterns import FullQualifiedId
from ..action import register_action
from ..action_interface import ActionPayload
from ..agenda_item.create import AgendaItemCreate
from ..base import DataSet
from ..default_schema import DefaultSchema
from ..generics import CreateAction


@register_action("topic.create")
class TopicCreate(CreateAction):
    """
    Action to create simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = DefaultSchema(Topic()).get_create_schema(
        properties=["meeting_id", "title", "text", "attachment_ids"],
        required_properties=["meeting_id", "title"],
    )

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        yield from super().create_write_request_elements(dataset)
        for topic_element in dataset["data"]:
            additional_relation_models = {
                FullQualifiedId(
                    Topic.collection, topic_element["new_id"]
                ): topic_element["instance"]
            }
            action = AgendaItemCreate(
                "agenda_item.create",
                self.permission,
                self.database,
                additional_relation_models,
            )
            agenda_item_payload: ActionPayload = [
                {
                    "meeting_id": topic_element["instance"]["meeting_id"],
                    "content_object_id": f"topic/{topic_element['new_id']}",
                }
            ]
            yield from action.perform(agenda_item_payload, self.user_id)

    # TODO: Automaticly add agenda item with extra fields.
    # "agenda_type",
    # "agenda_parent_id",
    # "agenda_comment",
    # "agenda_duration",
    # "agenda_weight",
    # The meeting settings agenda_item_creation is not evaluated. We always want to create the agenda item for topics.
