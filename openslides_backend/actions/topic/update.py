import fastjsonschema  # type: ignore
from fastjsonschema import JsonSchemaException  # type: ignore

from ...models.topic import Topic
from ...shared.exceptions import ActionException
from ...shared.schema import schema_version
from ..actions_interface import Payload
from ..base import Action, DataSet

is_valid_update_topic = fastjsonschema.compile(
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


# @register_action("topic.update")  # Tests still missing
class TopicUpdate(Action):
    """
    Action to update simple topics that can be shown in the agenda.
    """

    model = Topic()

    def validate(self, payload: Payload) -> None:
        try:
            is_valid_update_topic(payload)
        except JsonSchemaException as exception:
            raise ActionException(exception.message)

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for topic in payload:
            exists, position = self.database_adapter.exists(
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
