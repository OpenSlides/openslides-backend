from typing import Any, Dict, Iterable

from ....models.models import Meeting, Speaker
from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import Collection
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData


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

    def get_updated_instances(self, payload: ActionData) -> Iterable[Dict[str, Any]]:
        new_payload = []
        meeting_ids = [instance["id"] for instance in payload]
        get_many_request = GetManyRequest(
            Collection("meeting"), meeting_ids, ["list_of_speakers_ids"]
        )
        gm_result = self.datastore.get_many([get_many_request])
        meetings = gm_result.get(Collection("meeting"), {})

        los_ids = []
        for meeting in meetings.values():
            los_ids.extend(meeting.get("list_of_speakers_ids", []))
        get_many_request = GetManyRequest(
            Collection("list_of_speakers"), los_ids, ["speaker_ids"]
        )
        gm_result = self.datastore.get_many([get_many_request])
        lists_of_speakers = gm_result.get(Collection("list_of_speakers"), {})
        for los in lists_of_speakers.values():
            for speaker in los.get("speaker_ids", []):
                new_payload.append({"id": speaker})
        return new_payload
