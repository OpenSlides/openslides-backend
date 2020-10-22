from typing import Any, Dict, Iterable

from ...models.models import Meeting, Speaker
from ...shared.exceptions import NoContentException
from ...shared.patterns import Collection, FullQualifiedId
from ..default_schema import DefaultSchema
from ..generics import ActionPayload, DeleteAction
from ..register import register_action


@register_action("meeting.delete_all_speakers_of_all_lists")
class DeleteAllSpeakersOfAllListsAction(DeleteAction):
    """
    Action to delete all speakers of all lists of a meeting.
    """

    model = Speaker()  # we want to delete Speakers
    schema = DefaultSchema(Meeting()).get_default_schema(
        required_properties=["id"],
        title="Delete all speakers of all list of a meeting.",
        description="An array of meeting objects which speakers to be deleted",
    )

    def get_updated_instances(self, payload: ActionPayload) -> Iterable[Dict[str, Any]]:
        new_payload = []
        for instance in payload:
            meeting = self.database.get(
                FullQualifiedId(Collection("meeting"), instance["id"]),
                ["list_of_speakers_ids"],
            )
            if not meeting.get("list_of_speakers_ids"):
                continue
            for los in meeting["list_of_speakers_ids"]:
                list_of_speakers = self.database.get(
                    FullQualifiedId(Collection("list_of_speakers"), los),
                    ["speaker_ids"],
                )
                for speaker in list_of_speakers.get("speaker_ids", []):
                    new_payload.append({"id": speaker})
        if not new_payload:
            raise NoContentException("No speakers to delete.")
        return new_payload
