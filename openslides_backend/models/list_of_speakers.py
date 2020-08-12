from ..shared.patterns import Collection
from . import fields
from .base import Model


class ListOfSpeakers(Model):
    """
    Model for list of speakers.

    Reverse fields:
    - speakers_ids: (speaker/list_of_speakers_id)[];
    - projection_ids: (projection/element_id)[];
    - current_projector_ids: (projector/current_element_ids)[];
    - content_object_id: {motion,motion_block,assignment,topic,mediafile}/list_of_speakers_id;
    """

    collection = Collection("list_of_speakers")
    verbose_name = "list_of_speakers"

    id = fields.IdField(description="The id of this list of speakers.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this list of speakers.",
        to=Collection("meeting"),
        related_name="list_of_speakers_ids",
    )
    closed = fields.BooleanField(description="If the list of speakers is closed.")
