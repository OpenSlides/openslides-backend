from ....shared.filters import FilterOperator
from ...action import Action


class DuplicateCheckMixin(Action):
    def init_duplicate_set(self, meeting_id: int) -> None:
        self.all_titles_in_meeting = {
            values.get("title")
            for values in self.datastore.filter(
                "topic", FilterOperator("meeting_id", "=", meeting_id), ["title"]
            ).values()
        }

    def check_for_duplicate(self, title: str) -> bool:
        result = title in self.all_titles_in_meeting
        if not result:
            self.all_titles_in_meeting.add(title)
        return result
