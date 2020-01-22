from typing import Any, Iterable

import fastjsonschema  # type: ignore

from ...models.topic import Topic
from ...shared.exceptions import PermissionDenied
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedField, FullQualifiedId
from ...shared.permissions.topic import TOPIC_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..actions_interface import Payload
from ..base import Action, DataSet, merge_write_request_elements

update_topic_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Update topics schema",
        "description": "An array of topics to be updated.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": Topic().get_schema("id"),
                "title": Topic().get_schema("title"),
                "text": Topic().get_schema("text"),
                "mediafile_attachment_ids": Topic().get_schema(
                    "mediafile_attachment_ids"
                ),
            },
            "required": ["id"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("topic.update")
class TopicUpdate(Action):
    """
    Action to update simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = update_topic_schema

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
            references = self.get_references(
                model=self.model,
                id=topic["id"],
                obj=topic,
                fields=["mediafile_attachment_ids"],
                deletion_possible=True,
            )
            data.append({"topic": topic, "references": references})
        return {"position": self.position, "data": data}

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        position = dataset["position"]
        for element in dataset["data"]:
            topic_write_request_element = self.create_topic_write_request_element(
                position, element
            )
            for reference in self.get_references_updates(position, element):
                topic_write_request_element = merge_write_request_elements(
                    (topic_write_request_element, reference)
                )
            yield topic_write_request_element

    def create_topic_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        fqfields = {}
        for field in element["topic"].keys():
            if field == "id":
                continue
            fqfields[
                FullQualifiedField(self.model.collection, element["topic"]["id"], field)
            ] = element["topic"][field]
        information = {
            FullQualifiedId(self.model.collection, element["topic"]["id"]): [
                "Topic updated"
            ]
        }
        event = Event(type="update", fqfields=fqfields)
        return WriteRequestElement(
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={
                FullQualifiedField(
                    self.model.collection, element["topic"]["id"], "deleted"
                ): position
            },
        )

    def get_references_updates(
        self, position: int, element: Any
    ) -> Iterable[WriteRequestElement]:
        for fqfield, data in element["references"].items():
            event = Event(type="update", fqfields={fqfield: data["value"]})
            if data["type"] == "add":
                info_text = "Object attached to topic"
            else:
                # data["type"] == "remove"
                info_text = "Object attachment to topic reset"
            yield WriteRequestElement(
                events=[event],
                information={
                    FullQualifiedId(fqfield.collection, fqfield.id): [info_text]
                },
                user_id=self.user_id,
                locked_fields={fqfield: position},
            )
