from ....shared.exceptions import PermissionDenied
from ....shared.patterns import to_fqid
from ...action import Action


class PermissionMixin(Action):
    def check_anonymous_and_user_in_meeting(self, meeting_id: int) -> None:
        self.assert_not_anonymous()
        user = self.datastore.get(to_fqid("user", self.user_id), ["meeting_ids"])
        if meeting_id not in user.get("meeting_ids", []):
            raise PermissionDenied("User not associated with meeting.")
