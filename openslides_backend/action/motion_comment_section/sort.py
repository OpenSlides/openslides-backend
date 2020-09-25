from typing import Iterable, List

from ...models.models import MotionCommentSection
from ...shared.exceptions import ActionException
from ...shared.filters import FilterOperator
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedId
from ..action import register_action
from ..base import Action, ActionPayload, DataSet
from ..default_schema import DefaultSchema


@register_action("motion_comment_section.sort")
class MotionCommentSectionSort(Action):
    """
    Action to sort motion comment sections.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_linear_sort_schema(
        "motion_comment_section_ids"
    )

    def sort_linear(self, nodes: List, meeting_id: int) -> DataSet:
        filter = FilterOperator("meeting_id", "=", meeting_id)
        db_instances = self.database.filter(
            collection=self.model.collection,
            filter=filter,
            mapped_fields=["id"],
            lock_result=True,
        )
        valid_instance_ids = []
        for id_ in nodes:
            if id_ not in db_instances:
                raise ActionException(
                    f"Id {id_} not in db_instances of meeting {meeting_id}."
                )
            valid_instance_ids.append(id_)
        if len(valid_instance_ids) != len(db_instances):
            raise ActionException("Additional db_instances not found.")

        data = dict()
        weight = 1
        for id_ in valid_instance_ids:
            data[id_] = {"weight": weight}
            weight += 1
        return {"data": data}

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        if not isinstance(payload, dict):
            raise TypeError("ActionPayload for this action must be a dictionary.")
        return self.sort_linear(
            nodes=payload["motion_comment_section_ids"],
            meeting_id=payload["meeting_id"],
        )

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        for id, instance in dataset["data"].items():
            fqid = FullQualifiedId(self.model.collection, id)
            information = {fqid: ["Object sorted"]}
            event = Event(type="update", fqid=fqid, fields=instance)
            # TODO: Lock some fields to protect against intermediate creation of new instances but care where exactly to lock them.
            yield WriteRequestElement(
                events=[event], information=information, user_id=self.user_id
            )
