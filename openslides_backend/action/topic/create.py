from typing import Iterable, cast

from ...models.agenda_item import AgendaItem
from ...models.fields import RelationMixin
from ...models.topic import Topic
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedId
from ..action import register_action
from ..action_interface import ActionPayload
from ..base import DataSet, DataSetElement
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

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        dataset = super().prepare_dataset(payload)
        agenda_items = []
        for topic_element in dataset["data"]:
            agenda_item_element = self.create_agenda_item_element(topic_element)
            agenda_items.append(agenda_item_element)
            topic_element["instance"]["agenda_item_id"] = agenda_item_element["new_id"]
        dataset["agenda_items"] = agenda_items
        return dataset

    def create_agenda_item_element(
        self, topic_element: DataSetElement
    ) -> DataSetElement:
        instance = {}
        field_name = "meeting_id"
        instance[field_name] = topic_element["instance"][field_name]
        instance["content_object_id"] = FullQualifiedId(
            collection=self.model.collection, id=topic_element["new_id"]
        )
        new_id = self.database.reserve_id(collection=AgendaItem().collection)
        relation_fields = [
            (field_name, cast(RelationMixin, AgendaItem().get_field(field_name)), False)
        ]
        relations = self.get_relations(
            model=AgendaItem(),
            id=new_id,
            obj=instance,
            relation_fields=relation_fields,
            shortcut=True,
        )
        return {"instance": instance, "new_id": new_id, "relations": relations}

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        yield from super().create_write_request_elements(dataset)
        for agenda_item in dataset["agenda_items"]:
            yield self.create_agenda_item_instance_write_request_element(agenda_item)
            yield from self.get_relations_updates(agenda_item, model=AgendaItem())

    def create_agenda_item_instance_write_request_element(
        self, agenda_item: DataSetElement,
    ) -> WriteRequestElement:
        fqid = FullQualifiedId(AgendaItem().collection, agenda_item["new_id"])
        information = {fqid: ["Object created"]}
        event = Event(type="create", fqid=fqid, fields=agenda_item["instance"])
        return WriteRequestElement(
            events=[event], information=information, user_id=self.user_id
        )

    # TODO: Automaticly add agenda item with extra fields.
    # "agenda_type",
    # "agenda_parent_id",
    # "agenda_comment",
    # "agenda_duration",
    # "agenda_weight",
    # The meeting settings agenda_item_creation is not evaluated. We always want to create the agenda item for topics.
